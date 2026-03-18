import math
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


BG = '#f4f7fb'
CARD = '#ffffff'
PRIMARY = '#4f46e5'
PRIMARY_DARK = '#3730a3'
ACCENT = '#06b6d4'
SUCCESS = '#10b981'
TEXT = '#1f2937'
MUTED = '#6b7280'
GRID = '#d7deea'
ORIGINAL_COLOR = '#94a3b8'
TRANSFORMED_COLOR = '#4f46e5'


class MatrixDialog(tk.Toplevel):
    def __init__(self, master, title, get_matrix_callback):
        super().__init__(master)
        self.get_matrix_callback = get_matrix_callback
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())

        container = tk.Frame(self, bg=BG, padx=14, pady=14)
        container.pack(fill='both', expand=True)

        self.title_label = tk.Label(
            container,
            text=title,
            bg=BG,
            fg=TEXT,
            font=('Segoe UI', 12, 'bold'),
        )
        self.title_label.pack(anchor='w', pady=(0, 10))

        self.grid_frame = tk.Frame(container, bg=BG)
        self.grid_frame.pack()

        self.cells = []
        matrix = self.get_matrix_callback()
        rows, cols = matrix.shape
        for i in range(rows):
            row = []
            for j in range(cols):
                lbl = tk.Label(
                    self.grid_frame,
                    text='0.00',
                    width=9,
                    height=2,
                    bg=CARD,
                    fg=TEXT,
                    relief='flat',
                    bd=0,
                    font=('Consolas', 10, 'bold'),
                    highlightthickness=1,
                    highlightbackground='#dbe4f0',
                )
                lbl.grid(row=i, column=j, padx=4, pady=4, sticky='nsew')
                row.append(lbl)
            self.cells.append(row)

        btns = tk.Frame(container, bg=BG)
        btns.pack(fill='x', pady=(12, 0))

        refresh = tk.Button(
            btns,
            text='Atualizar',
            bg=ACCENT,
            fg='white',
            activebackground='#0891b2',
            activeforeground='white',
            relief='flat',
            padx=12,
            pady=8,
            font=('Segoe UI', 9, 'bold'),
            command=self.refresh,
            cursor='hand2',
        )
        refresh.pack(side='left')

        close = tk.Button(
            btns,
            text='Fechar',
            bg=PRIMARY,
            fg='white',
            activebackground=PRIMARY_DARK,
            activeforeground='white',
            relief='flat',
            padx=12,
            pady=8,
            font=('Segoe UI', 9, 'bold'),
            command=self.destroy,
            cursor='hand2',
        )
        close.pack(side='right')

        self.refresh()

    def refresh(self):
        matrix = self.get_matrix_callback()
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                self.cells[i][j].configure(text=f'{matrix[i, j]:.2f}')


class StyledCard(tk.Frame):
    def __init__(self, master, title):
        super().__init__(master, bg=CARD, highlightthickness=1, highlightbackground='#dbe4f0')
        header = tk.Frame(self, bg=CARD)
        header.pack(fill='x', padx=12, pady=(10, 6))

        tk.Label(
            header,
            text=title,
            bg=CARD,
            fg=TEXT,
            font=('Segoe UI', 11, 'bold'),
        ).pack(anchor='w')

        self.body = tk.Frame(self, bg=CARD)
        self.body.pack(fill='both', expand=True, padx=12, pady=(0, 12))


class Transform2DTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.original_points = np.array([
            [-1.0, -1.0, 1.0],
            [1.0, -1.0, 1.0],
            [1.0, 1.0, 1.0],
            [-1.0, 1.0, 1.0],
        ])
        self.current_transform = np.eye(3)
        self.view_xlim = [-6.0, 6.0]
        self.view_ylim = [-6.0, 6.0]
        self.current_matrix_dialog = None

        self._build_ui()
        self._bind_updates()
        self.update_status()
        self.redraw()

    def _build_ui(self):
        self.configure(style='App.TFrame')

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill='both', expand=True, padx=12, pady=12)

        left = tk.Frame(outer, bg=BG, width=390)
        left.pack(side='left', fill='y', padx=(0, 12))
        left.pack_propagate(False)

        center = tk.Frame(outer, bg=BG)
        center.pack(side='left', fill='both', expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg=BG, width=300)
        right.pack(side='left', fill='y')
        right.pack_propagate(False)

        info = StyledCard(left, 'Configurações gerais')
        info.pack(fill='x', pady=(0, 12))

        self.keep_original_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            info.body,
            text='Manter objeto original visível',
            variable=self.keep_original_var,
            command=self.redraw,
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            activeforeground=TEXT,
            selectcolor='white',
            font=('Segoe UI', 10),
        ).pack(anchor='w')

        self._build_transform_card(
            left,
            'Translação 2D',
            [('Tx', '1', 'tx_var'), ('Ty', '1', 'ty_var')],
            self.apply_translation,
            self.get_translation_matrix,
            'Transladar',
        )
        self._build_transform_card(
            left,
            'Escala 2D',
            [('Sx', '1.5', 'sx_var'), ('Sy', '1.5', 'sy_var')],
            self.apply_scale,
            self.get_scale_matrix,
            'Escalar',
        )
        self._build_transform_card(
            left,
            'Rotação 2D',
            [('Ângulo (graus)', '30', 'angle_var')],
            self.apply_rotation,
            self.get_rotation_matrix,
            'Rotacionar',
        )

        actions = StyledCard(left, 'Ações')
        actions.pack(fill='x')
        btn_row = tk.Frame(actions.body, bg=CARD)
        btn_row.pack(fill='x')
        self._nice_button(btn_row, 'Resetar transformações', self.reset, SUCCESS).pack(fill='x')

        graph_card = StyledCard(center, 'Plano cartesiano')
        graph_card.pack(fill='both', expand=True)

        top_controls = tk.Frame(graph_card.body, bg=CARD)
        top_controls.pack(fill='x', pady=(0, 8))

        view_box = tk.Frame(top_controls, bg='#eef2ff', padx=10, pady=8)
        view_box.pack(side='left', fill='x', expand=True)

        tk.Label(view_box, text='Janela de visualização fixa', bg='#eef2ff', fg=TEXT, font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=8, sticky='w', pady=(0, 6))

        self.xmin2d_var = tk.StringVar(value='-6')
        self.xmax2d_var = tk.StringVar(value='6')
        self.ymin2d_var = tk.StringVar(value='-6')
        self.ymax2d_var = tk.StringVar(value='6')

        for idx, (label, var) in enumerate([
            ('X min', self.xmin2d_var), ('X max', self.xmax2d_var), ('Y min', self.ymin2d_var), ('Y max', self.ymax2d_var)
        ]):
            tk.Label(view_box, text=label, bg='#eef2ff', fg=MUTED, font=('Segoe UI', 9)).grid(row=1 + idx // 2, column=(idx % 2) * 2, sticky='w', padx=(0, 4), pady=2)
            tk.Entry(view_box, textvariable=var, width=8, relief='flat', font=('Segoe UI', 9)).grid(row=1 + idx // 2, column=(idx % 2) * 2 + 1, padx=(0, 12), pady=2)

        self._nice_button(view_box, 'Aplicar janela', self.apply_2d_limits, PRIMARY).grid(row=3, column=0, columnspan=2, sticky='ew', pady=(8, 0), padx=(0, 8))
        self._nice_button(view_box, 'Zoom +', lambda: self.zoom_2d(0.8), ACCENT).grid(row=3, column=2, sticky='ew', pady=(8, 0), padx=4)
        self._nice_button(view_box, 'Zoom -', lambda: self.zoom_2d(1.25), ACCENT).grid(row=3, column=3, sticky='ew', pady=(8, 0), padx=4)
        self._nice_button(view_box, 'Centralizar', self.center_2d_view, '#8b5cf6').grid(row=3, column=4, sticky='ew', pady=(8, 0), padx=4)

        fig = Figure(figsize=(7.5, 7), dpi=100)
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(fig, master=graph_card.body)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, graph_card.body, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(fill='x', pady=(6, 0))

        matrix_card = StyledCard(right, 'Matriz acumulada')
        matrix_card.pack(fill='x', pady=(0, 12))
        self.accumulated_summary_2d = tk.Label(
            matrix_card.body,
            text='',
            justify='left',
            bg=CARD,
            fg=TEXT,
            font=('Consolas', 10, 'bold'),
        )
        self.accumulated_summary_2d.pack(anchor='w', pady=(0, 10))
        self._nice_button(
            matrix_card.body,
            'Abrir matriz acumulada',
            lambda: self.open_matrix_dialog('Matriz acumulada 2D', lambda: self.current_transform),
            PRIMARY,
        ).pack(fill='x')

        vertices_card = StyledCard(right, 'Vértices atuais')
        vertices_card.pack(fill='both', expand=True)
        self.vertex_labels_2d = []
        for i, name in enumerate(['A', 'B', 'C', 'D']):
            row = tk.Frame(vertices_card.body, bg=CARD)
            row.pack(fill='x', pady=3)
            tk.Label(row, text=name, width=3, bg='#eef2ff', fg=PRIMARY_DARK, font=('Segoe UI', 9, 'bold')).pack(side='left')
            lbl = tk.Label(row, text='(0.00, 0.00)', bg=CARD, fg=TEXT, font=('Consolas', 10))
            lbl.pack(side='left', padx=8)
            self.vertex_labels_2d.append(lbl)

    def _build_transform_card(self, parent, title, fields, apply_command, matrix_callback, button_text):
        card = StyledCard(parent, title)
        card.pack(fill='x', pady=(0, 12))

        for i, (label, default, attr_name) in enumerate(fields):
            var = tk.StringVar(value=default)
            setattr(self, attr_name, var)
            tk.Label(card.body, text=label, bg=CARD, fg=MUTED, font=('Segoe UI', 9)).grid(row=i, column=0, sticky='w', pady=4)
            entry = tk.Entry(card.body, textvariable=var, relief='flat', font=('Segoe UI', 10), width=12)
            entry.grid(row=i, column=1, sticky='ew', padx=(8, 0), pady=4)

        card.body.columnconfigure(1, weight=1)

        btns = tk.Frame(card.body, bg=CARD)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky='ew', pady=(8, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        self._nice_button(btns, button_text, apply_command, PRIMARY).grid(row=0, column=0, sticky='ew', padx=(0, 4))
        self._nice_button(btns, 'Ver matriz', lambda cb=matrix_callback, t=title: self.open_matrix_dialog(f'{t} - matriz', cb), ACCENT).grid(row=0, column=1, sticky='ew', padx=(4, 0))

    def _nice_button(self, parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            activebackground=color,
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=12,
            pady=10,
            font=('Segoe UI', 9, 'bold'),
            cursor='hand2',
        )

    def _bind_updates(self):
        for var in [self.tx_var, self.ty_var, self.sx_var, self.sy_var, self.angle_var]:
            var.trace_add('write', lambda *_: self.refresh_matrix_dialog())

    def _safe_float(self, value, default=0.0):
        try:
            return float(value.replace(',', '.'))
        except Exception:
            return default

    def get_translation_matrix(self):
        tx = self._safe_float(self.tx_var.get(), 0.0)
        ty = self._safe_float(self.ty_var.get(), 0.0)
        return np.array([[1.0, 0.0, tx], [0.0, 1.0, ty], [0.0, 0.0, 1.0]])

    def get_scale_matrix(self):
        sx = self._safe_float(self.sx_var.get(), 1.0)
        sy = self._safe_float(self.sy_var.get(), 1.0)
        return np.array([[sx, 0.0, 0.0], [0.0, sy, 0.0], [0.0, 0.0, 1.0]])

    def get_rotation_matrix(self):
        angle = math.radians(self._safe_float(self.angle_var.get(), 0.0))
        c = math.cos(angle)
        s = math.sin(angle)
        return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])

    def apply_translation(self):
        self.current_transform = self.get_translation_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def apply_scale(self):
        self.current_transform = self.get_scale_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def apply_rotation(self):
        self.current_transform = self.get_rotation_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def transformed_points(self):
        return (self.current_transform @ self.original_points.T).T

    def apply_2d_limits(self):
        xmin = self._safe_float(self.xmin2d_var.get(), -6)
        xmax = self._safe_float(self.xmax2d_var.get(), 6)
        ymin = self._safe_float(self.ymin2d_var.get(), -6)
        ymax = self._safe_float(self.ymax2d_var.get(), 6)
        if xmax <= xmin:
            xmax = xmin + 1
        if ymax <= ymin:
            ymax = ymin + 1
        self.view_xlim = [xmin, xmax]
        self.view_ylim = [ymin, ymax]
        self.redraw()

    def zoom_2d(self, factor):
        cx = (self.view_xlim[0] + self.view_xlim[1]) / 2
        cy = (self.view_ylim[0] + self.view_ylim[1]) / 2
        hx = (self.view_xlim[1] - self.view_xlim[0]) * factor / 2
        hy = (self.view_ylim[1] - self.view_ylim[0]) * factor / 2
        self.view_xlim = [cx - hx, cx + hx]
        self.view_ylim = [cy - hy, cy + hy]
        self._sync_2d_limit_entries()
        self.redraw()

    def center_2d_view(self):
        width = self.view_xlim[1] - self.view_xlim[0]
        height = self.view_ylim[1] - self.view_ylim[0]
        self.view_xlim = [-width / 2, width / 2]
        self.view_ylim = [-height / 2, height / 2]
        self._sync_2d_limit_entries()
        self.redraw()

    def _sync_2d_limit_entries(self):
        self.xmin2d_var.set(f'{self.view_xlim[0]:.2f}')
        self.xmax2d_var.set(f'{self.view_xlim[1]:.2f}')
        self.ymin2d_var.set(f'{self.view_ylim[0]:.2f}')
        self.ymax2d_var.set(f'{self.view_ylim[1]:.2f}')

    def open_matrix_dialog(self, title, callback):
        if self.current_matrix_dialog and self.current_matrix_dialog.winfo_exists():
            self.current_matrix_dialog.destroy()
        self.current_matrix_dialog = MatrixDialog(self, title, callback)

    def refresh_matrix_dialog(self):
        if self.current_matrix_dialog and self.current_matrix_dialog.winfo_exists():
            self.current_matrix_dialog.refresh()

    def update_status(self):
        self.accumulated_summary_2d.configure(text=self._matrix_text(self.current_transform))
        self.refresh_matrix_dialog()

    def _matrix_text(self, matrix):
        return '\n'.join('  '.join(f'{value:7.2f}' for value in row) for row in matrix)

    def reset(self):
        self.current_transform = np.eye(3)
        self.update_status()
        self.redraw()

    def redraw(self):
        self.ax.clear()
        self.ax.set_title('Transformações Geométricas 2D', fontsize=13, color=TEXT, pad=12)
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_facecolor('#fbfdff')
        self.ax.axhline(0, color='#64748b', linewidth=1.2)
        self.ax.axvline(0, color='#64748b', linewidth=1.2)
        self.ax.grid(True, linestyle='--', linewidth=0.8, color=GRID)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(self.view_xlim)
        self.ax.set_ylim(self.view_ylim)

        current = self.transformed_points()

        if self.keep_original_var.get():
            base = np.vstack([self.original_points[:, :2], self.original_points[0, :2]])
            self.ax.plot(base[:, 0], base[:, 1], linestyle='--', linewidth=2, color=ORIGINAL_COLOR, label='Original')
            self.ax.scatter(self.original_points[:, 0], self.original_points[:, 1], s=50, color=ORIGINAL_COLOR)

        cur = np.vstack([current[:, :2], current[0, :2]])
        self.ax.plot(cur[:, 0], cur[:, 1], linewidth=2.8, color=TRANSFORMED_COLOR, label='Transformado')
        self.ax.scatter(current[:, 0], current[:, 1], s=60, color=TRANSFORMED_COLOR)

        for i, (label, point) in enumerate(zip(['A', 'B', 'C', 'D'], current)):
            x, y = point[:2]
            self.ax.text(x + 0.12, y + 0.12, f'{label} ({x:.2f}, {y:.2f})', fontsize=9, color=TEXT)
            self.vertex_labels_2d[i].configure(text=f'({x:.2f}, {y:.2f})')

        self.ax.legend(loc='upper right', frameon=True)
        self.canvas.draw_idle()


class Transform3DTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.original_points = np.array([
            [-1.0, -1.0, -1.0, 1.0],
            [1.0, -1.0, -1.0, 1.0],
            [1.0, 1.0, -1.0, 1.0],
            [-1.0, 1.0, -1.0, 1.0],
            [-1.0, -1.0, 1.0, 1.0],
            [1.0, -1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0],
            [-1.0, 1.0, 1.0, 1.0],
        ])
        self.current_transform = np.eye(4)
        self.view_limits = [-6.0, 6.0]
        self.current_matrix_dialog = None

        self._build_ui()
        self._bind_updates()
        self.update_status()
        self.redraw()

    def _build_ui(self):
        self.configure(style='App.TFrame')

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill='both', expand=True, padx=12, pady=12)

        left = tk.Frame(outer, bg=BG, width=400)
        left.pack(side='left', fill='y', padx=(0, 12))
        left.pack_propagate(False)

        center = tk.Frame(outer, bg=BG)
        center.pack(side='left', fill='both', expand=True, padx=(0, 12))

        right = tk.Frame(outer, bg=BG, width=320)
        right.pack(side='left', fill='y')
        right.pack_propagate(False)

        info = StyledCard(left, 'Configurações gerais')
        info.pack(fill='x', pady=(0, 12))

        self.keep_original_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            info.body,
            text='Manter objeto original visível',
            variable=self.keep_original_var,
            command=self.redraw,
            bg=CARD,
            fg=TEXT,
            activebackground=CARD,
            activeforeground=TEXT,
            selectcolor='white',
            font=('Segoe UI', 10),
        ).pack(anchor='w')

        self._build_transform_card(
            left,
            'Translação 3D',
            [('Tx', '1', 't3x_var'), ('Ty', '1', 't3y_var'), ('Tz', '1', 't3z_var')],
            self.apply_translation,
            self.get_translation_matrix,
            'Transladar',
        )
        self._build_transform_card(
            left,
            'Escala 3D',
            [('Sx', '1.2', 's3x_var'), ('Sy', '1.2', 's3y_var'), ('Sz', '1.2', 's3z_var')],
            self.apply_scale,
            self.get_scale_matrix,
            'Escalar',
        )

        rot_card = StyledCard(left, 'Rotações 3D')
        rot_card.pack(fill='x', pady=(0, 12))
        for i, (label, default, attr) in enumerate([
            ('Ângulo X', '20', 'rx_var'), ('Ângulo Y', '20', 'ry_var'), ('Ângulo Z', '20', 'rz_var')
        ]):
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            tk.Label(rot_card.body, text=label, bg=CARD, fg=MUTED, font=('Segoe UI', 9)).grid(row=i, column=0, sticky='w', pady=4)
            tk.Entry(rot_card.body, textvariable=var, relief='flat', font=('Segoe UI', 10), width=10).grid(row=i, column=1, sticky='ew', padx=(8, 0), pady=4)

        rot_card.body.columnconfigure(1, weight=1)
        btns = tk.Frame(rot_card.body, bg=CARD)
        btns.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(8, 0))
        for c in range(3):
            btns.columnconfigure(c, weight=1)
        self._nice_button(btns, 'Rotacionar X', self.apply_rotation_x, PRIMARY).grid(row=0, column=0, sticky='ew', padx=(0, 4))
        self._nice_button(btns, 'Rotacionar Y', self.apply_rotation_y, PRIMARY).grid(row=0, column=1, sticky='ew', padx=4)
        self._nice_button(btns, 'Rotacionar Z', self.apply_rotation_z, PRIMARY).grid(row=0, column=2, sticky='ew', padx=(4, 0))

        btns2 = tk.Frame(rot_card.body, bg=CARD)
        btns2.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(8, 0))
        for c in range(3):
            btns2.columnconfigure(c, weight=1)
        self._nice_button(btns2, 'Ver matriz X', lambda: self.open_matrix_dialog('Rotação X - matriz', self.get_rotation_x_matrix), ACCENT).grid(row=0, column=0, sticky='ew', padx=(0, 4))
        self._nice_button(btns2, 'Ver matriz Y', lambda: self.open_matrix_dialog('Rotação Y - matriz', self.get_rotation_y_matrix), ACCENT).grid(row=0, column=1, sticky='ew', padx=4)
        self._nice_button(btns2, 'Ver matriz Z', lambda: self.open_matrix_dialog('Rotação Z - matriz', self.get_rotation_z_matrix), ACCENT).grid(row=0, column=2, sticky='ew', padx=(4, 0))

        actions = StyledCard(left, 'Ações')
        actions.pack(fill='x')
        self._nice_button(actions.body, 'Resetar transformações', self.reset, SUCCESS).pack(fill='x')

        graph_card = StyledCard(center, 'Espaço 3D')
        graph_card.pack(fill='both', expand=True)

        top_controls = tk.Frame(graph_card.body, bg=CARD)
        top_controls.pack(fill='x', pady=(0, 8))

        view_box = tk.Frame(top_controls, bg='#eef2ff', padx=10, pady=8)
        view_box.pack(side='left', fill='x', expand=True)
        tk.Label(view_box, text='Janela de visualização fixa', bg='#eef2ff', fg=TEXT, font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=6, sticky='w', pady=(0, 6))

        self.min3d_var = tk.StringVar(value='-6')
        self.max3d_var = tk.StringVar(value='6')
        tk.Label(view_box, text='Mínimo', bg='#eef2ff', fg=MUTED, font=('Segoe UI', 9)).grid(row=1, column=0, sticky='w', padx=(0, 4))
        tk.Entry(view_box, textvariable=self.min3d_var, width=8, relief='flat', font=('Segoe UI', 9)).grid(row=1, column=1, padx=(0, 12))
        tk.Label(view_box, text='Máximo', bg='#eef2ff', fg=MUTED, font=('Segoe UI', 9)).grid(row=1, column=2, sticky='w', padx=(0, 4))
        tk.Entry(view_box, textvariable=self.max3d_var, width=8, relief='flat', font=('Segoe UI', 9)).grid(row=1, column=3, padx=(0, 12))

        self._nice_button(view_box, 'Aplicar janela', self.apply_3d_limits, PRIMARY).grid(row=2, column=0, columnspan=2, sticky='ew', pady=(8, 0), padx=(0, 8))
        self._nice_button(view_box, 'Zoom +', lambda: self.zoom_3d(0.8), ACCENT).grid(row=2, column=2, sticky='ew', pady=(8, 0), padx=4)
        self._nice_button(view_box, 'Zoom -', lambda: self.zoom_3d(1.25), ACCENT).grid(row=2, column=3, sticky='ew', pady=(8, 0), padx=4)
        self._nice_button(view_box, 'Centralizar', self.center_3d_view, '#8b5cf6').grid(row=2, column=4, sticky='ew', pady=(8, 0), padx=4)

        fig = Figure(figsize=(8.3, 7), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(fig, master=graph_card.body)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, graph_card.body, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(fill='x', pady=(6, 0))

        matrix_card = StyledCard(right, 'Matriz acumulada')
        matrix_card.pack(fill='x', pady=(0, 12))
        self.accumulated_summary_3d = tk.Label(
            matrix_card.body,
            text='',
            justify='left',
            bg=CARD,
            fg=TEXT,
            font=('Consolas', 9, 'bold'),
        )
        self.accumulated_summary_3d.pack(anchor='w', pady=(0, 10))
        self._nice_button(
            matrix_card.body,
            'Abrir matriz acumulada',
            lambda: self.open_matrix_dialog('Matriz acumulada 3D', lambda: self.current_transform),
            PRIMARY,
        ).pack(fill='x')

        vertices_card = StyledCard(right, 'Vértices atuais')
        vertices_card.pack(fill='both', expand=True)
        self.vertex_labels_3d = []
        for i in range(8):
            row = tk.Frame(vertices_card.body, bg=CARD)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=f'V{i}', width=4, bg='#ecfeff', fg='#155e75', font=('Segoe UI', 9, 'bold')).pack(side='left')
            lbl = tk.Label(row, text='(0.00, 0.00, 0.00)', bg=CARD, fg=TEXT, font=('Consolas', 9))
            lbl.pack(side='left', padx=8)
            self.vertex_labels_3d.append(lbl)

    def _build_transform_card(self, parent, title, fields, apply_command, matrix_callback, button_text):
        card = StyledCard(parent, title)
        card.pack(fill='x', pady=(0, 12))
        for i, (label, default, attr_name) in enumerate(fields):
            var = tk.StringVar(value=default)
            setattr(self, attr_name, var)
            tk.Label(card.body, text=label, bg=CARD, fg=MUTED, font=('Segoe UI', 9)).grid(row=i, column=0, sticky='w', pady=4)
            tk.Entry(card.body, textvariable=var, relief='flat', font=('Segoe UI', 10), width=12).grid(row=i, column=1, sticky='ew', padx=(8, 0), pady=4)
        card.body.columnconfigure(1, weight=1)

        btns = tk.Frame(card.body, bg=CARD)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky='ew', pady=(8, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        self._nice_button(btns, button_text, apply_command, PRIMARY).grid(row=0, column=0, sticky='ew', padx=(0, 4))
        self._nice_button(btns, 'Ver matriz', lambda cb=matrix_callback, t=title: self.open_matrix_dialog(f'{t} - matriz', cb), ACCENT).grid(row=0, column=1, sticky='ew', padx=(4, 0))

    def _nice_button(self, parent, text, command, color):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            activebackground=color,
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=12,
            pady=10,
            font=('Segoe UI', 9, 'bold'),
            cursor='hand2',
        )

    def _bind_updates(self):
        for var in [self.t3x_var, self.t3y_var, self.t3z_var, self.s3x_var, self.s3y_var, self.s3z_var, self.rx_var, self.ry_var, self.rz_var]:
            var.trace_add('write', lambda *_: self.refresh_matrix_dialog())

    def _safe_float(self, value, default=0.0):
        try:
            return float(value.replace(',', '.'))
        except Exception:
            return default

    def get_translation_matrix(self):
        tx = self._safe_float(self.t3x_var.get(), 0.0)
        ty = self._safe_float(self.t3y_var.get(), 0.0)
        tz = self._safe_float(self.t3z_var.get(), 0.0)
        return np.array([[1.0, 0.0, 0.0, tx], [0.0, 1.0, 0.0, ty], [0.0, 0.0, 1.0, tz], [0.0, 0.0, 0.0, 1.0]])

    def get_scale_matrix(self):
        sx = self._safe_float(self.s3x_var.get(), 1.0)
        sy = self._safe_float(self.s3y_var.get(), 1.0)
        sz = self._safe_float(self.s3z_var.get(), 1.0)
        return np.array([[sx, 0.0, 0.0, 0.0], [0.0, sy, 0.0, 0.0], [0.0, 0.0, sz, 0.0], [0.0, 0.0, 0.0, 1.0]])

    def get_rotation_x_matrix(self):
        angle = math.radians(self._safe_float(self.rx_var.get(), 0.0))
        c = math.cos(angle)
        s = math.sin(angle)
        return np.array([[1.0, 0.0, 0.0, 0.0], [0.0, c, -s, 0.0], [0.0, s, c, 0.0], [0.0, 0.0, 0.0, 1.0]])

    def get_rotation_y_matrix(self):
        angle = math.radians(self._safe_float(self.ry_var.get(), 0.0))
        c = math.cos(angle)
        s = math.sin(angle)
        return np.array([[c, 0.0, s, 0.0], [0.0, 1.0, 0.0, 0.0], [-s, 0.0, c, 0.0], [0.0, 0.0, 0.0, 1.0]])

    def get_rotation_z_matrix(self):
        angle = math.radians(self._safe_float(self.rz_var.get(), 0.0))
        c = math.cos(angle)
        s = math.sin(angle)
        return np.array([[c, -s, 0.0, 0.0], [s, c, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])

    def apply_translation(self):
        self.current_transform = self.get_translation_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def apply_scale(self):
        self.current_transform = self.get_scale_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def apply_rotation_x(self):
        self.current_transform = self.get_rotation_x_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def apply_rotation_y(self):
        self.current_transform = self.get_rotation_y_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def apply_rotation_z(self):
        self.current_transform = self.get_rotation_z_matrix() @ self.current_transform
        self.update_status()
        self.redraw()

    def transformed_points(self):
        return (self.current_transform @ self.original_points.T).T

    def apply_3d_limits(self):
        min_v = self._safe_float(self.min3d_var.get(), -6)
        max_v = self._safe_float(self.max3d_var.get(), 6)
        if max_v <= min_v:
            max_v = min_v + 1
        self.view_limits = [min_v, max_v]
        self.redraw()

    def zoom_3d(self, factor):
        center = (self.view_limits[0] + self.view_limits[1]) / 2
        half = (self.view_limits[1] - self.view_limits[0]) * factor / 2
        self.view_limits = [center - half, center + half]
        self._sync_3d_limit_entries()
        self.redraw()

    def center_3d_view(self):
        size = self.view_limits[1] - self.view_limits[0]
        self.view_limits = [-size / 2, size / 2]
        self._sync_3d_limit_entries()
        self.redraw()

    def _sync_3d_limit_entries(self):
        self.min3d_var.set(f'{self.view_limits[0]:.2f}')
        self.max3d_var.set(f'{self.view_limits[1]:.2f}')

    def open_matrix_dialog(self, title, callback):
        if self.current_matrix_dialog and self.current_matrix_dialog.winfo_exists():
            self.current_matrix_dialog.destroy()
        self.current_matrix_dialog = MatrixDialog(self, title, callback)

    def refresh_matrix_dialog(self):
        if self.current_matrix_dialog and self.current_matrix_dialog.winfo_exists():
            self.current_matrix_dialog.refresh()

    def update_status(self):
        self.accumulated_summary_3d.configure(text=self._matrix_text(self.current_transform))
        self.refresh_matrix_dialog()

    def _matrix_text(self, matrix):
        return '\n'.join('  '.join(f'{value:6.2f}' for value in row) for row in matrix)

    def reset(self):
        self.current_transform = np.eye(4)
        self.update_status()
        self.redraw()

    def _cube_faces(self, points_xyz):
        return [
            [points_xyz[0], points_xyz[1], points_xyz[2], points_xyz[3]],
            [points_xyz[4], points_xyz[5], points_xyz[6], points_xyz[7]],
            [points_xyz[0], points_xyz[1], points_xyz[5], points_xyz[4]],
            [points_xyz[2], points_xyz[3], points_xyz[7], points_xyz[6]],
            [points_xyz[1], points_xyz[2], points_xyz[6], points_xyz[5]],
            [points_xyz[4], points_xyz[7], points_xyz[3], points_xyz[0]],
        ]

    def redraw(self):
        self.ax.clear()
        self.ax.set_title('Transformações Geométricas 3D', fontsize=13, color=TEXT, pad=12)
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_facecolor('#fbfdff')
        self.ax.set_xlim(self.view_limits)
        self.ax.set_ylim(self.view_limits)
        self.ax.set_zlim(self.view_limits)
        size = self.view_limits[1] - self.view_limits[0]
        self.ax.set_box_aspect((size, size, size))

        current = self.transformed_points()
        current_xyz = current[:, :3]

        if self.keep_original_var.get():
            orig = self.original_points[:, :3]
            original_poly = Poly3DCollection(self._cube_faces(orig), alpha=0.10, linewidths=1.0, edgecolors=ORIGINAL_COLOR, facecolors=ORIGINAL_COLOR)
            self.ax.add_collection3d(original_poly)
            self.ax.scatter(orig[:, 0], orig[:, 1], orig[:, 2], s=24, color=ORIGINAL_COLOR)

        current_poly = Poly3DCollection(self._cube_faces(current_xyz), alpha=0.25, linewidths=1.5, edgecolors=TRANSFORMED_COLOR, facecolors='#818cf8')
        self.ax.add_collection3d(current_poly)
        self.ax.scatter(current_xyz[:, 0], current_xyz[:, 1], current_xyz[:, 2], s=36, color=TRANSFORMED_COLOR)

        for i, (x, y, z) in enumerate(current_xyz):
            self.ax.text(x, y, z, f'V{i}', color=TEXT, fontsize=8)
            self.vertex_labels_3d[i].configure(text=f'({x:.2f}, {y:.2f}, {z:.2f})')

        self.canvas.draw_idle()


class TransformApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Transformações Geométricas 2D e 3D')
        self.geometry('1660x940')
        self.minsize(1450, 860)
        self.configure(bg=BG)

        self._configure_style()
        self._build_ui()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('App.TFrame', background=BG)
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', padding=(18, 10), font=('Segoe UI', 11, 'bold'))

    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill='both', expand=True)

        header = tk.Frame(root, bg=PRIMARY, height=72)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text='Transformações Geométricas',
            bg=PRIMARY,
            fg='white',
            font=('Segoe UI', 18, 'bold'),
        ).pack(side='left', padx=18)

        tk.Label(
            header,
            text='2D e 3D com matrizes homogêneas acumuladas',
            bg=PRIMARY,
            fg='#dbeafe',
            font=('Segoe UI', 10),
        ).pack(side='left', padx=(0, 12), pady=(6, 0))

        notebook = ttk.Notebook(root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        tab2d = Transform2DTab(notebook)
        tab3d = Transform3DTab(notebook)

        notebook.add(tab2d, text='2D')
        notebook.add(tab3d, text='3D')


if __name__ == '__main__':
    app = TransformApp()
    app.mainloop()
