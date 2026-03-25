
import math
import random
import tkinter as tk
from tkinter import ttk, colorchooser


class Vec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, k):
        return Vec3(self.x * k, self.y * k, self.z * k)

    __rmul__ = __mul__

    def __truediv__(self, k):
        return Vec3(self.x / k, self.y / k, self.z / k)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def length(self):
        return math.sqrt(self.dot(self))

    def normalized(self):
        l = self.length()
        if l == 0:
            return Vec3(0, 0, 0)
        return self / l

    def reflect(self, n):
        return self - n * (2.0 * self.dot(n))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def color_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return (
        int(hex_color[0:2], 16) / 255.0,
        int(hex_color[2:4], 16) / 255.0,
        int(hex_color[4:6], 16) / 255.0,
    )


def rgb_to_hex(rgb):
    r = int(clamp(rgb[0]) * 255)
    g = int(clamp(rgb[1]) * 255)
    b = int(clamp(rgb[2]) * 255)
    return f'#{r:02x}{g:02x}{b:02x}'


class Material:
    def __init__(self, color='#d14b4b', reflectivity=0.25, specular=0.7, shininess=32):
        self.color = color
        self.reflectivity = reflectivity
        self.specular = specular
        self.shininess = shininess


class Sphere:
    def __init__(self, name, center, radius, material):
        self.name = name
        self.center = center
        self.radius = radius
        self.material = material

    def intersect(self, ro, rd):
        oc = ro - self.center
        a = rd.dot(rd)
        b = 2.0 * oc.dot(rd)
        c = oc.dot(oc) - self.radius * self.radius
        disc = b * b - 4.0 * a * c
        if disc < 0:
            return None
        s = math.sqrt(disc)
        t1 = (-b - s) / (2.0 * a)
        t2 = (-b + s) / (2.0 * a)
        eps = 1e-4
        t = None
        if t1 > eps:
            t = t1
        elif t2 > eps:
            t = t2
        if t is None:
            return None
        p = ro + rd * t
        n = (p - self.center).normalized()
        return {'t': t, 'point': p, 'normal': n, 'obj': self}


class RayTeachingApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Demonstração de Ray Casting, Ray Tracing e Path Tracing')
        self.root.geometry('1460x940')
        self.root.minsize(1280, 820)
        self.root.configure(bg='#0b1020')

        self.setup_style()
        self.make_scene()
        self.make_state()
        self.build_ui()
        self.populate_entity_controls()

        self.root.after(80, self.draw_everything)

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#0b1020', foreground='#edf2ff')
        style.configure('Card.TFrame', background='#121936')
        style.configure('Panel.TLabelframe', background='#121936', foreground='#ffffff')
        style.configure('Panel.TLabelframe.Label', background='#121936', foreground='#ffffff')
        style.configure('TLabel', background='#121936', foreground='#e7ecff')
        style.configure('Header.TLabel', background='#0b1020', foreground='#ffffff', font=('Segoe UI', 18, 'bold'))
        style.configure('Sub.TLabel', background='#0b1020', foreground='#afbbe6', font=('Segoe UI', 10))
        style.configure('TButton', background='#4f7cff', foreground='#ffffff', padding=8, borderwidth=0)
        style.map('TButton', background=[('active', '#6990ff')])
        style.configure('TCheckbutton', background='#121936', foreground='#edf2ff')
        style.configure('TCombobox', fieldbackground='#151d35', background='#151d35', foreground='#ffffff')

    def make_scene(self):
        self.camera_pos = Vec3(0, 0, -8)
        self.image_plane_z = -2.0
        self.light_pos = Vec3(2.8, 3.5, -0.5)
        self.background_color = '#0f162c'

        self.spheres = [
            Sphere('Esfera 1', Vec3(-2.6, -0.8, 4.0), 1.15, Material('#ff6b6b', 0.15, 0.75, 48)),
            Sphere('Esfera 2', Vec3(1.2, 1.1, 5.8), 1.35, Material('#4dd0e1', 0.55, 0.90, 90)),
            Sphere('Esfera 3', Vec3(3.5, -1.2, 7.3), 1.55, Material('#f7c948', 0.05, 0.35, 20)),
        ]

        self.viewport_yaw = math.radians(32)
        self.viewport_pitch = math.radians(-18)
        self.viewer_distance = 18.0
        self.viewer_scale = 560.0

    def make_state(self):
        self.mode_var = tk.StringVar(value='Ray Casting')
        self.local_illum_var = tk.BooleanVar(value=True)
        self.diffuse_var = tk.BooleanVar(value=True)
        self.specular_var = tk.BooleanVar(value=True)
        self.shadow_var = tk.BooleanVar(value=True)
        self.reflection_var = tk.BooleanVar(value=True)
        self.show_axes_var = tk.BooleanVar(value=True)
        self.show_floor_var = tk.BooleanVar(value=True)
        self.live_update_var = tk.BooleanVar(value=True)

        self.max_depth_var = tk.IntVar(value=3)
        self.path_bounces_var = tk.IntVar(value=4)
        self.path_samples_var = tk.IntVar(value=8)
        self.ray_speed_var = tk.DoubleVar(value=1.0)

        self.grid_cols_var = tk.IntVar(value=14)
        self.grid_rows_var = tk.IntVar(value=10)
        self.plane_w_var = tk.DoubleVar(value=6.4)
        self.plane_h_var = tk.DoubleVar(value=4.6)

        self.view_yaw_var = tk.DoubleVar(value=32.0)
        self.view_pitch_var = tk.DoubleVar(value=-18.0)
        self.view_zoom_var = tk.DoubleVar(value=18.0)

        self.selected_pixel = (6, 4)
        self.pixel_colors = {}
        self.current_ray_segments = []
        self.is_animating = False
        self.current_animation_token = 0

        self.last_trace_active = False
        self.last_trace_pixel = None
        self.last_trace_color = None
        self.last_trace_message = ''
        self.last_trace_was_full_grid = False

        self.entity_var = tk.StringVar(value='Câmera')
        self.pos_x_var = tk.DoubleVar(value=0.0)
        self.pos_y_var = tk.DoubleVar(value=0.0)
        self.pos_z_var = tk.DoubleVar(value=0.0)
        self.radius_var = tk.DoubleVar(value=1.0)
        self.reflectivity_var = tk.DoubleVar(value=0.2)
        self.shininess_var = tk.DoubleVar(value=32.0)
        self.entity_color_var = tk.StringVar(value='#ffffff')

    def build_ui(self):
        outer = tk.Frame(self.root, bg='#0b1020')
        outer.pack(fill='both', expand=True, padx=18, pady=18)

        header = tk.Frame(outer, bg='#0b1020')
        header.pack(fill='x', pady=(0, 12))

        ttk.Label(header, text='Demonstração interativa de raios', style='Header.TLabel').pack(anchor='w')
        ttk.Label(
            header,
            text='Cena 3D com câmera, grid de pixels, luz e objetos. Selecione um pixel, dispare e compare os métodos.',
            style='Sub.TLabel'
        ).pack(anchor='w', pady=(2, 0))

        content = tk.Frame(outer, bg='#0b1020')
        content.pack(fill='both', expand=True)

        left = tk.Frame(content, bg='#0b1020')
        left.pack(side='left', fill='both', expand=True)

        right = ttk.Frame(content, style='Card.TFrame', width=390)
        right.pack(side='right', fill='y', padx=(18, 0))
        right.pack_propagate(False)

        scene_card = tk.Frame(left, bg='#121936', highlightthickness=1, highlightbackground='#263152')
        scene_card.pack(fill='both', expand=True)

        title_row = tk.Frame(scene_card, bg='#121936')
        title_row.pack(fill='x', padx=14, pady=(12, 6))
        tk.Label(title_row, text='Cena 3D', font=('Segoe UI', 13, 'bold'), fg='#ffffff', bg='#121936').pack(side='left')
        tk.Label(title_row, text='Esquerda: espaço 3D. Direita: grid/pixels.', font=('Segoe UI', 9), fg='#b7c2ea', bg='#121936').pack(side='right')

        views = tk.Frame(scene_card, bg='#121936')
        views.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        self.scene_canvas = tk.Canvas(views, width=840, height=640, bg='#0e1427', highlightthickness=0)
        self.scene_canvas.pack(side='left', fill='both', expand=True)
        self.scene_canvas.bind('<Configure>', lambda e: self.draw_everything())
        self.scene_canvas.focus_set()
        self.scene_canvas.bind('<Left>', lambda e: self.nudge_view(-8, 0))
        self.scene_canvas.bind('<Right>', lambda e: self.nudge_view(8, 0))
        self.scene_canvas.bind('<Up>', lambda e: self.nudge_view(0, -6))
        self.scene_canvas.bind('<Down>', lambda e: self.nudge_view(0, 6))
        self.scene_canvas.bind('<MouseWheel>', self.on_mousewheel_zoom)

        self.pixel_canvas = tk.Canvas(views, width=320, height=640, bg='#111830', highlightthickness=0)
        self.pixel_canvas.pack(side='left', fill='y', padx=(12, 0))
        self.pixel_canvas.bind('<Button-1>', self.on_pixel_canvas_click)
        self.pixel_canvas.bind('<Configure>', lambda e: self.draw_everything())

        self.build_controls(right)

    def build_controls(self, parent):
        shell = tk.Frame(parent, bg='#121936')
        shell.pack(fill='both', expand=True)

        canvas = tk.Canvas(shell, bg='#121936', highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        inner = tk.Frame(canvas, bg='#121936')
        window_id = canvas.create_window((0, 0), window=inner, anchor='nw')

        def on_inner_config(_):
            canvas.configure(scrollregion=canvas.bbox('all'))

        def on_canvas_config(event):
            canvas.itemconfigure(window_id, width=event.width)

        inner.bind('<Configure>', on_inner_config)
        canvas.bind('<Configure>', on_canvas_config)

        def _wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

        canvas.bind_all('<MouseWheel>', _wheel)

        mode_box = ttk.LabelFrame(inner, text='Modo', style='Panel.TLabelframe')
        mode_box.pack(fill='x', padx=14, pady=(14, 10))

        mode_combo = ttk.Combobox(mode_box, textvariable=self.mode_var, state='readonly',
                                  values=['Ray Casting', 'Ray Tracing', 'Path Tracing'])
        mode_combo.pack(fill='x', padx=10, pady=10)
        mode_combo.bind('<<ComboboxSelected>>', lambda e: self.on_visual_params_changed())

        row = tk.Frame(mode_box, bg='#121936')
        row.pack(fill='x', padx=10, pady=(0, 10))
        ttk.Button(row, text='Disparar pixel', command=self.animate_selected_pixel).pack(side='left', fill='x', expand=True)
        ttk.Button(row, text='Limpar raios', command=self.clear_rays).pack(side='left', fill='x', expand=True, padx=(8, 0))

        render_box = ttk.LabelFrame(inner, text='Opções do método', style='Panel.TLabelframe')
        render_box.pack(fill='x', padx=14, pady=(0, 10))

        for text, var in [
            ('Iluminação local', self.local_illum_var),
            ('Difuso', self.diffuse_var),
            ('Especular', self.specular_var),
            ('Shadow ray / sombras', self.shadow_var),
            ('Reflexão (Ray Tracing)', self.reflection_var),
            ('Atualização em tempo real após disparo', self.live_update_var),
        ]:
            ttk.Checkbutton(render_box, text=text, variable=var, command=self.on_visual_params_changed).pack(anchor='w', padx=10, pady=(8 if text == 'Iluminação local' else 0, 0))

        self.add_labeled_scale(render_box, 'Recursões máximas', self.max_depth_var, 0, 6, self.on_visual_params_changed)
        self.add_labeled_scale(render_box, 'Samples por pixel (Path)', self.path_samples_var, 1, 24, self.on_visual_params_changed)
        self.add_labeled_scale(render_box, 'Bounces máximos (Path)', self.path_bounces_var, 1, 8, self.on_visual_params_changed)
        self.add_labeled_scale(render_box, 'Velocidade do raio', self.ray_speed_var, 0.2, 3.0, self.draw_everything, resolution=0.1)

        grid_box = ttk.LabelFrame(inner, text='Grid de pixels', style='Panel.TLabelframe')
        grid_box.pack(fill='x', padx=14, pady=(0, 10))
        self.add_labeled_scale(grid_box, 'Colunas', self.grid_cols_var, 4, 24, self.on_grid_change)
        self.add_labeled_scale(grid_box, 'Linhas', self.grid_rows_var, 4, 18, self.on_grid_change)
        self.add_labeled_scale(grid_box, 'Largura do plano', self.plane_w_var, 3.0, 10.0, self.on_visual_params_changed, resolution=0.1)
        self.add_labeled_scale(grid_box, 'Altura do plano', self.plane_h_var, 2.0, 8.0, self.on_visual_params_changed, resolution=0.1)

        buttons = tk.Frame(grid_box, bg='#121936')
        buttons.pack(fill='x', padx=10, pady=(4, 10))
        ttk.Button(buttons, text='Renderizar grid inteira', command=self.render_full_grid).pack(side='left', fill='x', expand=True)
        ttk.Button(buttons, text='Cena padrão', command=self.reset_scene).pack(side='left', fill='x', expand=True, padx=(8, 0))

        view_box = ttk.LabelFrame(inner, text='Visualização da cena', style='Panel.TLabelframe')
        view_box.pack(fill='x', padx=14, pady=(0, 10))
        self.add_labeled_scale(view_box, 'Ângulo horizontal', self.view_yaw_var, -180, 180, self.update_view)
        self.add_labeled_scale(view_box, 'Ângulo vertical', self.view_pitch_var, -80, 80, self.update_view)
        self.add_labeled_scale(view_box, 'Zoom da visualização', self.view_zoom_var, 10, 32, self.update_view, resolution=0.5)
        ttk.Checkbutton(view_box, text='Mostrar eixos X/Y/Z', variable=self.show_axes_var, command=self.draw_everything).pack(anchor='w', padx=10, pady=(8, 0))
        ttk.Checkbutton(view_box, text='Mostrar piso guia', variable=self.show_floor_var, command=self.draw_everything).pack(anchor='w', padx=10, pady=(0, 10))
        hint = tk.Label(view_box, text='Use também as setas do teclado sobre a cena e a rodinha do mouse.',
                        fg='#b7c2ea', bg='#121936', font=('Segoe UI', 9))
        hint.pack(anchor='w', padx=10, pady=(0, 10))

        entity_box = ttk.LabelFrame(inner, text='Transformações da cena', style='Panel.TLabelframe')
        entity_box.pack(fill='x', padx=14, pady=(0, 10))

        entity_combo = ttk.Combobox(
            entity_box, textvariable=self.entity_var, state='readonly',
            values=['Câmera', 'Luz', 'Esfera 1', 'Esfera 2', 'Esfera 3']
        )
        entity_combo.pack(fill='x', padx=10, pady=10)
        entity_combo.bind('<<ComboboxSelected>>', lambda e: self.populate_entity_controls())

        self.add_labeled_scale(entity_box, 'Posição X', self.pos_x_var, -6.0, 6.0, self.apply_entity_changes, resolution=0.1)
        self.add_labeled_scale(entity_box, 'Posição Y', self.pos_y_var, -5.0, 5.0, self.apply_entity_changes, resolution=0.1)
        self.add_labeled_scale(entity_box, 'Posição Z', self.pos_z_var, -10.0, 12.0, self.apply_entity_changes, resolution=0.1)
        self.add_labeled_scale(entity_box, 'Raio', self.radius_var, 0.4, 3.0, self.apply_entity_changes, resolution=0.05)
        self.add_labeled_scale(entity_box, 'Refletividade', self.reflectivity_var, 0.0, 1.0, self.apply_entity_changes, resolution=0.05)
        self.add_labeled_scale(entity_box, 'Brilho especular', self.shininess_var, 2, 128, self.apply_entity_changes)

        color_row = tk.Frame(entity_box, bg='#121936')
        color_row.pack(fill='x', padx=10, pady=(4, 10))
        ttk.Button(color_row, text='Trocar cor', command=self.pick_entity_color).pack(side='left')
        self.color_preview = tk.Label(color_row, text='      ', bg='#ffffff', relief='flat')
        self.color_preview.pack(side='left', padx=(10, 0))

        info_box = ttk.LabelFrame(inner, text='Pixel selecionado', style='Panel.TLabelframe')
        info_box.pack(fill='both', expand=True, padx=14, pady=(0, 14))
        self.info_label = tk.Label(
            info_box, text='Clique em um pixel do grid à direita.', justify='left', anchor='nw',
            padx=10, pady=10, font=('Consolas', 10), fg='#dfe7ff', bg='#121936'
        )
        self.info_label.pack(fill='both', expand=True)

    def add_labeled_scale(self, parent, label, variable, frm, to, command, resolution=1):
        wrap = tk.Frame(parent, bg='#121936')
        wrap.pack(fill='x', padx=10, pady=(0, 8))

        row = tk.Frame(wrap, bg='#121936')
        row.pack(fill='x')
        tk.Label(row, text=label, fg='#dfe7ff', bg='#121936', font=('Segoe UI', 9)).pack(side='left')
        tk.Label(row, textvariable=variable, fg='#8ea9ff', bg='#121936', font=('Consolas', 9)).pack(side='right')

        scale = tk.Scale(
            wrap, from_=frm, to=to, resolution=resolution, orient='horizontal',
            variable=variable, showvalue=False, command=lambda _=None: command(),
            bg='#121936', fg='#dfe7ff', troughcolor='#263152',
            highlightthickness=0, activebackground='#4f7cff', relief='flat'
        )
        scale.pack(fill='x')

    def update_view(self):
        self.viewport_yaw = math.radians(self.view_yaw_var.get())
        self.viewport_pitch = math.radians(self.view_pitch_var.get())
        self.viewer_distance = self.view_zoom_var.get()
        self.draw_everything()

    def nudge_view(self, yaw_delta, pitch_delta):
        self.view_yaw_var.set(self.view_yaw_var.get() + yaw_delta)
        self.view_pitch_var.set(clamp(self.view_pitch_var.get() + pitch_delta, -80, 80))
        self.update_view()

    def on_mousewheel_zoom(self, event):
        delta = -1 if event.delta < 0 else 1
        self.view_zoom_var.set(clamp(self.view_zoom_var.get() - delta, 10, 32))
        self.update_view()

    def selected_entity(self):
        name = self.entity_var.get()
        if name == 'Câmera':
            return 'camera', None
        if name == 'Luz':
            return 'light', None
        for s in self.spheres:
            if s.name == name:
                return 'sphere', s
        return 'camera', None

    def populate_entity_controls(self):
        kind, obj = self.selected_entity()
        if kind == 'camera':
            p = self.camera_pos
            self.pos_x_var.set(round(p.x, 2))
            self.pos_y_var.set(round(p.y, 2))
            self.pos_z_var.set(round(p.z, 2))
            self.radius_var.set(1.0)
            self.reflectivity_var.set(0.0)
            self.shininess_var.set(1.0)
            self.entity_color_var.set('#ffffff')
        elif kind == 'light':
            p = self.light_pos
            self.pos_x_var.set(round(p.x, 2))
            self.pos_y_var.set(round(p.y, 2))
            self.pos_z_var.set(round(p.z, 2))
            self.radius_var.set(0.4)
            self.reflectivity_var.set(0.0)
            self.shininess_var.set(1.0)
            self.entity_color_var.set('#ffd166')
        else:
            self.pos_x_var.set(round(obj.center.x, 2))
            self.pos_y_var.set(round(obj.center.y, 2))
            self.pos_z_var.set(round(obj.center.z, 2))
            self.radius_var.set(round(obj.radius, 2))
            self.reflectivity_var.set(round(obj.material.reflectivity, 2))
            self.shininess_var.set(round(obj.material.shininess, 2))
            self.entity_color_var.set(obj.material.color)
        self.color_preview.configure(bg=self.entity_color_var.get())
        self.draw_everything()

    def apply_entity_changes(self):
        kind, obj = self.selected_entity()
        pos = Vec3(self.pos_x_var.get(), self.pos_y_var.get(), self.pos_z_var.get())
        if kind == 'camera':
            self.camera_pos = pos
        elif kind == 'light':
            self.light_pos = pos
        else:
            obj.center = pos
            obj.radius = max(0.15, self.radius_var.get())
            obj.material.reflectivity = clamp(self.reflectivity_var.get())
            obj.material.shininess = max(1.0, self.shininess_var.get())
        self.recompute_live_trace()

    def pick_entity_color(self):
        kind, obj = self.selected_entity()
        if kind != 'sphere':
            return
        picked = colorchooser.askcolor(color=obj.material.color, title='Escolha a cor da esfera')
        if picked and picked[1]:
            obj.material.color = picked[1]
            self.entity_color_var.set(picked[1])
            self.color_preview.configure(bg=picked[1])
            self.recompute_live_trace()

    def reset_scene(self):
        self.make_scene()
        self.view_yaw_var.set(32.0)
        self.view_pitch_var.set(-18.0)
        self.view_zoom_var.set(18.0)
        self.pixel_colors.clear()
        self.current_ray_segments = []
        self.entity_var.set('Câmera')
        self.last_trace_active = False
        self.last_trace_was_full_grid = False
        self.last_trace_pixel = None
        self.last_trace_color = None
        self.last_trace_message = ''
        self.populate_entity_controls()
        self.update_view()
        self.info_label.configure(text='Clique em um pixel do grid à direita.')

    def on_grid_change(self):
        cols = max(1, int(round(self.grid_cols_var.get())))
        rows = max(1, int(round(self.grid_rows_var.get())))
        self.grid_cols_var.set(cols)
        self.grid_rows_var.set(rows)
        self.selected_pixel = (min(self.selected_pixel[0], cols - 1), min(self.selected_pixel[1], rows - 1))
        self.pixel_colors = {}
        self.recompute_live_trace()

    def on_visual_params_changed(self):
        self.recompute_live_trace()

    def clear_rays(self):
        self.current_animation_token += 1
        self.is_animating = False
        self.current_ray_segments = []
        self.last_trace_active = False
        self.last_trace_was_full_grid = False
        self.last_trace_pixel = None
        self.last_trace_color = None
        self.last_trace_message = ''
        self.draw_everything()
        self.info_label.configure(text='Raios limpos.')

    def get_pixel_center(self, col, row):
        cols = int(self.grid_cols_var.get())
        rows = int(self.grid_rows_var.get())
        plane_w = self.plane_w_var.get()
        plane_h = self.plane_h_var.get()
        x = ((col + 0.5) / cols - 0.5) * plane_w
        y = (0.5 - (row + 0.5) / rows) * plane_h
        return Vec3(x, y, self.image_plane_z)

    def get_pixel_ray(self, col, row):
        pixel_center = self.get_pixel_center(col, row)
        rd = (pixel_center - self.camera_pos).normalized()
        return pixel_center, rd

    def find_closest_hit(self, ro, rd):
        closest = None
        best_t = 1e18
        for sph in self.spheres:
            hit = sph.intersect(ro, rd)
            if hit and hit['t'] < best_t:
                best_t = hit['t']
                closest = hit
        return closest

    def is_in_shadow(self, point):
        to_light = self.light_pos - point
        dist = to_light.length()
        rd = to_light.normalized()
        start = point + rd * 1e-3
        for sph in self.spheres:
            hit = sph.intersect(start, rd)
            if hit and hit['t'] < dist:
                return True
        return False

    def local_shading(self, hit, view_dir):
        mat = hit['obj'].material
        base = color_to_rgb(mat.color)
        p = hit['point']
        n = hit['normal']
        l = (self.light_pos - p).normalized()
        h = (l + view_dir).normalized()

        if not self.local_illum_var.get():
            return base, [], False

        shadow_visual = []
        shadowed = False
        if self.shadow_var.get():
            shadowed = self.is_in_shadow(p)
            shadow_color = '#ff7b7b' if shadowed else '#ffd166'
            shadow_visual.append((p, self.light_pos, shadow_color, 'shadow'))

        ambient = 0.08
        diffuse = 0.0
        specular = 0.0
        if not shadowed:
            if self.diffuse_var.get():
                diffuse = max(0.0, n.dot(l))
            if self.specular_var.get():
                specular = (max(0.0, n.dot(h)) ** mat.shininess) * mat.specular

        lit = tuple(clamp(base[i] * (ambient + 0.92 * diffuse) + specular) for i in range(3))
        return lit, shadow_visual, shadowed

    def trace_ray_tracing(self, ro, rd, depth):
        visual_segments = []
        hit = self.find_closest_hit(ro, rd)
        if not hit:
            return color_to_rgb(self.background_color), visual_segments

        p = hit['point']
        n = hit['normal']
        view_dir = (self.camera_pos - p).normalized()
        local_color, local_rays, _ = self.local_shading(hit, view_dir)
        visual_segments.extend(local_rays)

        result = local_color
        if self.reflection_var.get() and depth > 0 and hit['obj'].material.reflectivity > 0:
            refl_dir = rd.reflect(n).normalized()
            refl_hit = self.find_closest_hit(p + refl_dir * 1e-3, refl_dir)
            refl_end = refl_hit['point'] if refl_hit else (p + refl_dir * 10.0)
            visual_segments.append((p, refl_end, '#9b7bff', 'reflection'))
            refl_color, child_segments = self.trace_ray_tracing(p + refl_dir * 1e-3, refl_dir, depth - 1)
            visual_segments.extend(child_segments)
            kr = hit['obj'].material.reflectivity
            result = tuple(clamp(local_color[i] * (1.0 - kr) + refl_color[i] * kr) for i in range(3))
        return result, visual_segments

    def random_hemisphere_dir(self, normal):
        while True:
            d = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
            if d.length() < 1e-6 or d.length() > 1.0:
                continue
            d = d.normalized()
            if d.dot(normal) < 0:
                d = d * -1
            return d

    def trace_path(self, ro, rd, bounces):
        visual_segments = []
        throughput = (1.0, 1.0, 1.0)
        accumulated = (0.0, 0.0, 0.0)

        curr_o = ro
        curr_d = rd

        for _ in range(bounces):
            hit = self.find_closest_hit(curr_o, curr_d)
            if not hit:
                bg = color_to_rgb(self.background_color)
                accumulated = tuple(accumulated[i] + throughput[i] * bg[i] for i in range(3))
                break

            p = hit['point']
            n = hit['normal']
            mat = hit['obj'].material
            base = color_to_rgb(mat.color)

            to_light = (self.light_pos - p).normalized()
            nl = max(0.0, n.dot(to_light))
            shadowed = self.shadow_var.get() and self.is_in_shadow(p)
            direct = tuple(base[i] * (0.08 + (0.85 * nl if not shadowed else 0.0)) for i in range(3))
            accumulated = tuple(accumulated[i] + throughput[i] * direct[i] for i in range(3))

            new_dir = self.random_hemisphere_dir(n)
            next_hit = self.find_closest_hit(p + new_dir * 1e-3, new_dir)
            seg_end = next_hit['point'] if next_hit else (p + new_dir * 9.0)
            visual_segments.append((p, seg_end, '#6ee7b7', 'path'))
            throughput = tuple(throughput[i] * base[i] * 0.92 for i in range(3))
            curr_o = p + new_dir * 1e-3
            curr_d = new_dir

        return tuple(clamp(c) for c in accumulated), visual_segments

    def evaluate_pixel(self, col, row):
        pixel_center, rd = self.get_pixel_ray(col, row)
        hit = self.find_closest_hit(self.camera_pos, rd)

        segments = [(self.camera_pos, pixel_center, '#7dd3fc', 'primary')]
        if hit:
            segments.append((pixel_center, hit['point'], '#7dd3fc', 'primary'))
        else:
            segments.append((pixel_center, pixel_center + rd * 10.0, '#7dd3fc', 'primary'))

        mode = self.mode_var.get()

        if mode == 'Ray Casting':
            if not hit:
                return color_to_rgb(self.background_color), segments, 'Sem interseção: cor de fundo.'
            local_color, local_rays, shadowed = self.local_shading(hit, (self.camera_pos - hit['point']).normalized())
            segments.extend(local_rays)
            msg = f'Interseção em {hit["obj"].name}.'
            if self.local_illum_var.get():
                extras = []
                if self.diffuse_var.get():
                    extras.append('difuso')
                if self.specular_var.get():
                    extras.append('especular')
                if self.shadow_var.get():
                    extras.append('shadow ray')
                    extras.append('em sombra' if shadowed else 'iluminado')
                if extras:
                    msg += ' ' + ', '.join(extras) + '.'
            else:
                msg += ' Apenas cor base do objeto.'
            return local_color, segments, msg

        if mode == 'Ray Tracing':
            color, more_segments = self.trace_ray_tracing(self.camera_pos, rd, int(self.max_depth_var.get()))
            segments.extend(more_segments)
            return color, segments, f'Ray Tracing com profundidade máxima = {int(self.max_depth_var.get())}.'

        samples = int(self.path_samples_var.get())
        bounces = int(self.path_bounces_var.get())
        acc = [0.0, 0.0, 0.0]
        sample_paths = []
        for _ in range(samples):
            c, more_segments = self.trace_path(self.camera_pos, rd, bounces)
            sample_paths.append(more_segments)
            acc[0] += c[0]
            acc[1] += c[1]
            acc[2] += c[2]
        color = (acc[0] / samples, acc[1] / samples, acc[2] / samples)
        if sample_paths:
            segments.extend(sample_paths[0])
        return color, segments, f'Path Tracing com {samples} samples e {bounces} bounces máximos.'

    def update_info_label(self):
        if self.last_trace_active and self.last_trace_pixel is not None and self.last_trace_color is not None:
            col, row = self.last_trace_pixel
            suffix = ' | grid inteira atualizada' if self.last_trace_was_full_grid else ''
            self.info_label.configure(
                text=(
                    f'Pixel selecionado: ({col}, {row})\n'
                    f'Modo: {self.mode_var.get()}\n'
                    f'{self.last_trace_message}{suffix}\n'
                    f'Cor final: {rgb_to_hex(self.last_trace_color)}'
                )
            )

    def recompute_live_trace(self):
        if self.is_animating:
            return

        if self.live_update_var.get() and self.last_trace_active and self.last_trace_pixel is not None:
            col, row = self.last_trace_pixel
            color, segments, msg = self.evaluate_pixel(col, row)
            self.current_ray_segments = segments
            self.last_trace_color = color
            self.last_trace_message = msg
            self.pixel_colors[(col, row)] = rgb_to_hex(color)
            if self.last_trace_was_full_grid:
                self.recompute_full_grid_silently()
            self.update_info_label()
            self.draw_everything()
        else:
            self.draw_everything()

    def recompute_full_grid_silently(self):
        cols = int(self.grid_cols_var.get())
        rows = int(self.grid_rows_var.get())
        for r in range(rows):
            for c in range(cols):
                color, _, _ = self.evaluate_pixel(c, r)
                self.pixel_colors[(c, r)] = rgb_to_hex(color)

    def animate_selected_pixel(self):
        if self.is_animating:
            return

        col, row = self.selected_pixel
        color, segments, msg = self.evaluate_pixel(col, row)
        self.current_ray_segments = []
        self.is_animating = True
        self.current_animation_token += 1
        token = self.current_animation_token

        delay_base = max(12, int(80 / max(0.2, self.ray_speed_var.get())))

        flat = []
        for a, b, color_hex, kind in segments:
            steps = 22 if kind == 'primary' else 16
            flat.append((a, b, color_hex, kind, steps))

        def reveal_segment(i):
            if token != self.current_animation_token:
                self.is_animating = False
                return
            if i >= len(flat):
                self.is_animating = False
                self.pixel_colors[(col, row)] = rgb_to_hex(color)
                self.current_ray_segments = segments
                self.last_trace_active = True
                self.last_trace_pixel = (col, row)
                self.last_trace_color = color
                self.last_trace_message = msg
                self.last_trace_was_full_grid = False
                self.update_info_label()
                self.draw_everything()
                return

            a, b, color_hex, kind, steps = flat[i]

            def reveal_step(step):
                if token != self.current_animation_token:
                    self.is_animating = False
                    return
                if step > steps:
                    self.current_ray_segments.append((a, b, color_hex, kind))
                    self.draw_everything()
                    self.root.after(max(10, delay_base // 2), lambda: reveal_segment(i + 1))
                    return
                t = step / steps
                mid = a + (b - a) * t
                self.draw_everything(temp_segment=(a, mid, color_hex, kind))
                self.root.after(delay_base, lambda: reveal_step(step + 1))

            reveal_step(1)

        reveal_segment(0)

    def render_full_grid(self):
        self.current_animation_token += 1
        self.is_animating = False
        self.current_ray_segments = []

        cols = int(self.grid_cols_var.get())
        rows = int(self.grid_rows_var.get())
        self.pixel_colors = {}
        for r in range(rows):
            for c in range(cols):
                color, _, _ = self.evaluate_pixel(c, r)
                self.pixel_colors[(c, r)] = rgb_to_hex(color)

        col, row = self.selected_pixel
        color, segments, msg = self.evaluate_pixel(col, row)
        self.current_ray_segments = segments
        self.last_trace_active = True
        self.last_trace_was_full_grid = True
        self.last_trace_pixel = (col, row)
        self.last_trace_color = color
        self.last_trace_message = msg
        self.update_info_label()
        self.draw_everything()

    def rotate_view(self, p):
        cy = math.cos(self.viewport_yaw)
        sy = math.sin(self.viewport_yaw)
        x1 = p.x * cy - p.z * sy
        z1 = p.x * sy + p.z * cy

        cp = math.cos(self.viewport_pitch)
        sp = math.sin(self.viewport_pitch)
        y2 = p.y * cp - z1 * sp
        z2 = p.y * sp + z1 * cp

        return Vec3(x1, y2, z2)

    def project_point(self, p, canvas_w, canvas_h):
        v = self.rotate_view(p)
        z = v.z + self.viewer_distance
        if z < 0.4:
            z = 0.4
        sx = canvas_w * 0.49 + (v.x / z) * self.viewer_scale
        sy = canvas_h * 0.53 - (v.y / z) * self.viewer_scale
        return sx, sy, z

    def plane_corners(self):
        w = self.plane_w_var.get()
        h = self.plane_h_var.get()
        z = self.image_plane_z
        return [
            Vec3(-w / 2, -h / 2, z),
            Vec3(w / 2, -h / 2, z),
            Vec3(w / 2, h / 2, z),
            Vec3(-w / 2, h / 2, z),
        ]

    def draw_background_gradient(self, canvas, w, h):
        steps = 32
        for i in range(steps):
            t = i / max(1, steps - 1)
            r = int((14 * (1 - t)) + (27 * t))
            g = int((20 * (1 - t)) + (36 * t))
            b = int((39 * (1 - t)) + (72 * t))
            color = f'#{r:02x}{g:02x}{b:02x}'
            y0 = int(h * i / steps)
            y1 = int(h * (i + 1) / steps)
            canvas.create_rectangle(0, y0, w, y1, fill=color, outline='')

    def draw_scene(self, temp_segment=None):
        c = self.scene_canvas
        c.delete('all')
        w = max(10, c.winfo_width())
        h = max(10, c.winfo_height())
        self.draw_background_gradient(c, w, h)

        if self.show_floor_var.get():
            floor_lines = []
            for gx in range(-8, 9):
                floor_lines.append((Vec3(gx, -3.0, -1), Vec3(gx, -3.0, 12)))
            for gz in range(-1, 13):
                floor_lines.append((Vec3(-8, -3.0, gz), Vec3(8, -3.0, gz)))
            for a, b in floor_lines:
                x1, y1, _ = self.project_point(a, w, h)
                x2, y2, _ = self.project_point(b, w, h)
                c.create_line(x1, y1, x2, y2, fill='#182241')

        if self.show_axes_var.get():
            for a, b, color, label in [
                (Vec3(0, 0, 0), Vec3(3, 0, 0), '#ff6b6b', 'X'),
                (Vec3(0, 0, 0), Vec3(0, 3, 0), '#4dd0e1', 'Y'),
                (Vec3(0, 0, 0), Vec3(0, 0, 3), '#ffd166', 'Z'),
            ]:
                x1, y1, _ = self.project_point(a, w, h)
                x2, y2, _ = self.project_point(b, w, h)
                c.create_line(x1, y1, x2, y2, fill=color, width=2)
                c.create_text(x2 + 8, y2, text=label, fill=color, font=('Segoe UI', 10, 'bold'))

        corners = self.plane_corners()
        pts = [self.project_point(p, w, h) for p in corners]
        poly = [(pts[i][0], pts[i][1]) for i in range(4)]
        c.create_polygon(poly, outline='#7aa2ff', fill='#1a274d', width=2, stipple='gray25')

        cols = int(self.grid_cols_var.get())
        rows = int(self.grid_rows_var.get())
        plane_w = self.plane_w_var.get()
        plane_h = self.plane_h_var.get()

        for i in range(1, cols):
            x = -plane_w / 2 + plane_w * i / cols
            a = Vec3(x, -plane_h / 2, self.image_plane_z)
            b = Vec3(x, plane_h / 2, self.image_plane_z)
            x1, y1, _ = self.project_point(a, w, h)
            x2, y2, _ = self.project_point(b, w, h)
            c.create_line(x1, y1, x2, y2, fill='#5f78bf')
        for j in range(1, rows):
            y = -plane_h / 2 + plane_h * j / rows
            a = Vec3(-plane_w / 2, y, self.image_plane_z)
            b = Vec3(plane_w / 2, y, self.image_plane_z)
            x1, y1, _ = self.project_point(a, w, h)
            x2, y2, _ = self.project_point(b, w, h)
            c.create_line(x1, y1, x2, y2, fill='#5f78bf')

        pc = self.get_pixel_center(*self.selected_pixel)
        px, py, _ = self.project_point(pc, w, h)
        c.create_oval(px - 6, py - 6, px + 6, py + 6, fill='#f8fafc', outline='#7dd3fc', width=2)
        c.create_text(px + 46, py - 12, text=f'pixel {self.selected_pixel}', fill='#dbe9ff', font=('Segoe UI', 10, 'bold'))

        cx, cy, _ = self.project_point(self.camera_pos, w, h)
        c.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill='#ffffff', outline='#89a7ff', width=2)
        c.create_text(cx, cy - 18, text='Câmera', fill='#ffffff', font=('Segoe UI', 10, 'bold'))

        lx, ly, _ = self.project_point(self.light_pos, w, h)
        c.create_oval(lx - 9, ly - 9, lx + 9, ly + 9, fill='#ffd166', outline='#fff1bf', width=2)
        c.create_text(lx + 8, ly - 18, text='Luz', fill='#fff3c4', font=('Segoe UI', 10, 'bold'))

        entries = []
        for sph in self.spheres:
            sx, sy, sz = self.project_point(sph.center, w, h)
            r = (sph.radius / sz) * self.viewer_scale
            entries.append((sz, sph, sx, sy, r))
        entries.sort(reverse=True)

        for _, sph, sx, sy, r in entries:
            c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=sph.material.color, outline='#f8fbff', width=2)
            c.create_oval(sx - r * 0.42, sy - r * 0.55, sx - r * 0.08, sy - r * 0.15, fill='#ffffff', outline='')
            c.create_text(sx, sy + r + 14, text=sph.name, fill='#dfe7ff', font=('Segoe UI', 10))

        rays = list(self.current_ray_segments)
        if temp_segment is not None:
            rays.append(temp_segment)

        for a, b, color_hex, kind in rays:
            x1, y1, _ = self.project_point(a, w, h)
            x2, y2, _ = self.project_point(b, w, h)
            width = 3 if kind == 'primary' else 2
            dash = None if kind in ('primary', 'reflection') else (5, 4)
            c.create_line(x1, y1, x2, y2, fill=color_hex, width=width, dash=dash)

        c.create_text(
            18, 18, anchor='nw',
            text=f'Modo: {self.mode_var.get()}    Grid: {int(self.grid_cols_var.get())}x{int(self.grid_rows_var.get())}    Pixel: {self.selected_pixel}',
            fill='#dbe9ff', font=('Segoe UI', 11, 'bold')
        )

    def draw_pixel_grid(self):
        c = self.pixel_canvas
        c.delete('all')
        w = max(10, c.winfo_width())
        h = max(10, c.winfo_height())

        c.create_rectangle(0, 0, w, h, fill='#111830', outline='')
        c.create_rectangle(12, 12, w - 12, 70, fill='#141f3d', outline='#24345f', width=1)
        c.create_text(24, 22, anchor='nw', text='Imagem / grid de pixels', fill='#ffffff', font=('Segoe UI', 12, 'bold'))
        c.create_text(24, 46, anchor='nw', text='Clique em um pixel para escolher o raio primário.', fill='#b8c6ef', font=('Segoe UI', 9))

        cols = int(self.grid_cols_var.get())
        rows = int(self.grid_rows_var.get())
        pad_x = 24
        pad_y = 96
        usable_w = w - pad_x * 2
        usable_h = h - pad_y - 24
        cell = min(usable_w / cols, usable_h / rows)
        grid_w = cell * cols
        grid_h = cell * rows
        x0 = (w - grid_w) / 2
        y0 = pad_y

        self.pixel_grid_rect = (x0, y0, x0 + grid_w, y0 + grid_h, cell)
        c.create_rectangle(x0 - 8, y0 - 8, x0 + grid_w + 8, y0 + grid_h + 8, fill='#0d1429', outline='#33446f', width=2)

        for r in range(rows):
            for col in range(cols):
                x1 = x0 + col * cell
                y1 = y0 + r * cell
                x2 = x1 + cell
                y2 = y1 + cell
                fill = self.pixel_colors.get((col, r), '#1a2340')
                c.create_rectangle(x1, y1, x2, y2, fill=fill, outline='#2d3c63')

        col, row = self.selected_pixel
        sx1 = x0 + col * cell
        sy1 = y0 + row * cell
        sx2 = sx1 + cell
        sy2 = sy1 + cell
        c.create_rectangle(sx1, sy1, sx2, sy2, outline='#ffffff', width=3)
        c.create_text(w / 2, y0 + grid_h + 24, text=f'Pixel selecionado: ({col}, {row})', fill='#dce6ff', font=('Segoe UI', 10, 'bold'))

        lx = 28
        ly = y0 + grid_h + 54
        items = [
            ('#7dd3fc', 'raio primário'),
            ('#ffd166', 'shadow ray sem bloqueio'),
            ('#ff7b7b', 'shadow ray bloqueado'),
            ('#9b7bff', 'reflexão'),
            ('#6ee7b7', 'caminho estocástico'),
        ]
        for i, (color_hex, label) in enumerate(items):
            yy = ly + i * 24
            c.create_line(lx, yy, lx + 26, yy, fill=color_hex, width=3)
            c.create_text(lx + 36, yy, anchor='w', text=label, fill='#c7d5ff', font=('Segoe UI', 9))

    def draw_everything(self, temp_segment=None):
        self.draw_scene(temp_segment=temp_segment)
        self.draw_pixel_grid()

    def on_pixel_canvas_click(self, event):
        if not hasattr(self, 'pixel_grid_rect'):
            return
        x0, y0, x1, y1, cell = self.pixel_grid_rect
        if not (x0 <= event.x <= x1 and y0 <= event.y <= y1):
            return
        col = int((event.x - x0) / cell)
        row = int((event.y - y0) / cell)
        cols = int(self.grid_cols_var.get())
        rows = int(self.grid_rows_var.get())
        col = max(0, min(cols - 1, col))
        row = max(0, min(rows - 1, row))
        self.selected_pixel = (col, row)
        if self.live_update_var.get() and self.last_trace_active:
            self.last_trace_pixel = self.selected_pixel
            self.recompute_live_trace()
        else:
            self.draw_everything()


def main():
    root = tk.Tk()
    app = RayTeachingApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
