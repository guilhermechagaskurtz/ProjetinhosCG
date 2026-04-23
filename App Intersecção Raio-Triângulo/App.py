import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ==========================================
# CONFIGURAÇÃO E ESTADO DA MÁQUINA DE PASSOS
# ==========================================
st.set_page_config(page_title="Visualizador Möller-Trumbore", layout="wide")

if 'step' not in st.session_state:
    st.session_state.step = 0
if 'status' not in st.session_state:
    st.session_state.status = "Em andamento"

def next_step():
    if st.session_state.step < 6:
        st.session_state.step += 1

def prev_step():
    if st.session_state.step > 0:
        st.session_state.step -= 1
        st.session_state.status = "Em andamento"

def reset_step():
    st.session_state.step = 0
    st.session_state.status = "Em andamento"

# ==========================================
# INTERFACE LATERAL (INPUTS)
# ==========================================
st.sidebar.title("Parâmetros da Cena")
st.sidebar.markdown("Defina os vértices do triângulo e a origem/direção do raio.")

def parse_input(label, default_val):
    val = st.sidebar.text_input(label, default_val)
    try:
        return np.array([float(x.strip()) for x in val.split(',')])
    except:
        return np.array([0.0, 0.0, 0.0])

st.sidebar.subheader("Triângulo")
v0 = parse_input("V0 (x, y, z)", "-1, -1, 0")
v1 = parse_input("V1 (x, y, z)", "1, -1, 0")
v2 = parse_input("V2 (x, y, z)", "0, 1, 0")

st.sidebar.subheader("Raio")
p0 = parse_input("Origem P0 (x, y, z)", "0, 0, 2")
d_input = parse_input("Direção d (x, y, z)", "0, 0, -1")
# Normalização da direção
norm_d = np.linalg.norm(d_input)
d = d_input / norm_d if norm_d != 0 else d_input

st.sidebar.divider()

# Controles de Passo
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    st.button("Anterior", on_click=prev_step, disabled=(st.session_state.step == 0))
with col2:
    st.button("Seguinte", on_click=next_step, disabled=(st.session_state.step == 6 or st.session_state.status != "Em andamento"))
with col3:
    st.button("Reiniciar", on_click=reset_step)

st.sidebar.progress(st.session_state.step / 6.0)

# ==========================================
# FUNÇÕES DE RENDERIZAÇÃO 3D (PLOTLY)
# ==========================================
def draw_vector(fig, origin, vec, color, name, is_active=False, is_dashed=False):
    end = origin + vec
    line_width = 8 if is_active else 3
    dash_style = 'dash' if is_dashed else 'solid'
    
    # Linha do vetor
    fig.add_trace(go.Scatter3d(
        x=[origin[0], end[0]], y=[origin[1], end[1]], z=[origin[2], end[2]],
        mode='lines',
        line=dict(color=color, width=line_width, dash=dash_style),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Ponta do vetor (marcador) e Label (texto)
    if not is_dashed:
        text_font = dict(size=14, color=color, family="Arial Black") if is_active else dict(size=10, color=color)
        fig.add_trace(go.Scatter3d(
            x=[end[0]], y=[end[1]], z=[end[2]],
            mode='markers+text',
            marker=dict(size=4 if is_active else 2, color=color, symbol='diamond'),
            text=[name],
            textposition="top center",
            textfont=text_font,
            name=name
        ))

fig = go.Figure()

# Desenhar Triângulo Base (Sempre visível)
fig.add_trace(go.Mesh3d(
    x=[v0[0], v1[0], v2[0]], y=[v0[1], v1[1], v2[1]], z=[v0[2], v1[2], v2[2]],
    i=[0], j=[1], k=[2],
    color='lightblue', opacity=0.3, name='Triângulo'
))
# Contorno do Triângulo
fig.add_trace(go.Scatter3d(
    x=[v0[0], v1[0], v2[0], v0[0]], y=[v0[1], v1[1], v2[1], v0[1]], z=[v0[2], v1[2], v2[2], v0[2]],
    mode='lines+text',
    line=dict(color='white', width=2),
    text=["V0", "V1", "V2", ""],
    textposition="bottom center",
    name='Bordas'
))

# Desenhar Raio Base (Sempre visível)
draw_vector(fig, p0, d * 5, 'red', 'd (Direção)', is_active=(st.session_state.step == 0))
fig.add_trace(go.Scatter3d(
    x=[p0[0]], y=[p0[1]], z=[p0[2]],
    mode='markers+text', marker=dict(color='red', size=5),
    text=["P0"], textposition="bottom center", name='Origem do Raio'
))

# ==========================================
# LÓGICA DO ALGORITMO E ATUALIZAÇÃO DA TELA
# ==========================================
st.title("Algoritmo de Möller-Trumbore")

# Layout principal
text_col, plot_col = st.columns([1, 2.5])

eps = 1e-8
e1 = v1 - v0
e2 = v2 - v0
h = np.cross(d, e2)
a = np.dot(e1, h)

with text_col:
    st.subheader(f"Passo {st.session_state.step}")
    
    if st.session_state.step == 0:
        st.markdown("**Setup Inicial**")
        st.markdown("Definimos os valores iniciais do triângulo e do raio. O aluno clica em 'Seguinte' para iniciar os passos do algoritmo.")
        st.latex(r"Triângulo: V_0, V_1, V_2")
        st.latex(r"Raio: P = P_0 + t\vec{d}")

    if st.session_state.step >= 1:
        active = (st.session_state.step == 1)
        if active:
            st.markdown("**1. Descobrir as arestas do triângulo**")
            st.markdown("- **e1 = V1 - V0** (É o vetor que desenha a borda do ponto 0 até o ponto 1).")
            st.markdown("- **e2 = V2 - V0** (É o vetor que desenha a borda do ponto 0 até o ponto 2).")
            st.markdown("**Por que fazemos isso?** Juntas, essas duas arestas definem perfeitamente o 'plano' onde o triângulo está deitado e o seu tamanho.")
            st.latex(r"e_1 = V_1 - V_0")
            st.latex(r"e_2 = V_2 - V_0")
            
        draw_vector(fig, v0, e1, '#00FF00', 'e1', is_active=active)
        draw_vector(fig, v0, e2, '#A020F0', 'e2', is_active=active)

    if st.session_state.step >= 2:
        active = (st.session_state.step == 2)
        if active:
            st.markdown("**2. Checar se o raio é paralelo ao triângulo**")
            st.markdown("- **h = d x e2** (Produto vetorial entre a direção do raio e a aresta e2): Cria um vetor perpendicular a ambos.")
            st.markdown("- **a = e1 · h** (Produto escalar da aresta e1 com o vetor h): Isso funciona como um 'determinante'. **a** mede o quanto a aresta e1 está alinhada com a direção perpendicular criada por h.")
            st.markdown("**Por que fazemos isso?** Se a variável **a** for igual a zero (ou quase zero), isso prova que o raio está deslizando paralelo ao triângulo e nunca vai perfurá-lo. Se for zero, paramos o cálculo aqui.")
            st.latex(r"\vec{h} = \vec{d} \times e_2")
            st.latex(r"a = e_1 \cdot \vec{h} = " + f"{a:.4f}")
            
            if abs(a) < eps:
                st.error("O raio desliza paralelo ao triângulo! Cálculo encerrado.")
                st.session_state.status = "Erro"
            else:
                st.success("O determinante é válido (não é paralelo).")
                
        draw_vector(fig, v0, h, '#FFA500', 'h', is_active=active)
        
        if active and np.linalg.norm(h) != 0:
            proj_length = np.dot(e1, h) / np.linalg.norm(h)
            h_normalized = h / np.linalg.norm(h)
            proj_vec = proj_length * h_normalized
            draw_vector(fig, v0 + e1, proj_vec - e1, 'gray', 'projeção(a)', is_active=False, is_dashed=True)

    if st.session_state.step >= 3 and abs(a) > eps:
        f = 1.0 / a
        s = p0 - v0
        active = (st.session_state.step == 3)
        if active:
            st.markdown("**3. Preparar o terreno para descobrir o local exato**")
            st.markdown("- **f = 1 / a** (O inverso do determinante): Usado para 'normalizar' a escala dos próximos cálculos matemáticos.")
            st.markdown("- **s = P0 - V0:** Um vetor que liga o primeiro ponto do triângulo diretamente à origem do raio.")
            st.latex(r"f = \frac{1}{a} = " + f"{f:.4f}")
            st.latex(r"\vec{s} = P_0 - V_0")
            
        draw_vector(fig, v0, s, '#FFFFFF', 's', is_active=active)

    if st.session_state.step >= 4 and abs(a) > eps:
        u = f * np.dot(s, h)
        u_vec = u * e1 
        
        active = (st.session_state.step == 4)
        if active:
            st.markdown("**4. Calcular a posição horizontal (Coordenada u)**")
            st.markdown("- **u = f * (s · h)**")
            st.markdown("**O que é 'u'?** Imagine que a aresta e1 é o eixo X do triângulo. A variável **u** diz onde o raio bateu nesse eixo. Para o impacto ser dentro do triângulo, u precisa ser entre 0 e 1. Se for negativo ou maior que 1, o raio passou longe e paramos o cálculo.")
            st.latex(r"u = f (\vec{s} \cdot \vec{h}) = " + f"{u:.4f}")
            
            if u < 0.0 or u > 1.0:
                st.error(f"O raio passou longe (u = {u:.4f}). Paramos o cálculo.")
                st.session_state.status = "Erro"
            else:
                st.success("Impacto na horizontal (u) válido!")
                
        if st.session_state.step >= 4 and (0.0 <= u <= 1.0):
            draw_vector(fig, v0, u_vec, '#00FFFF', 'u', is_active=active)

    if st.session_state.step >= 5 and abs(a) > eps and (0.0 <= u <= 1.0):
        q = np.cross(s, e1)
        v = f * np.dot(d, q)
        v_vec = v * e2 
        
        active = (st.session_state.step == 5)
        if active:
            st.markdown("**5. Calcular a posição vertical (Coordenada v)**")
            st.markdown("- **q = s x e1** (Produto vetorial entre o vetor s e a aresta e1): É um cálculo intermediário para descobrir o eixo restante.")
            st.markdown("- **v = f * (d · q)**")
            st.markdown("**O que é 'v'?** Imagine que a aresta e2 é o eixo Y do triângulo. A variável **v** diz onde o raio bateu nesse eixo.")
            st.markdown("**O teste final do triângulo:** Para bater dentro, **v** tem que ser maior que 0. Além disso, a soma **(u + v)** não pode passar de 1. Se a soma for maior que 1, significa que o raio atingiu o plano, mas caiu para 'fora' da linha imaginária (V1-V2) que fecha o triângulo.")
            st.latex(r"\vec{q} = \vec{s} \times e_1")
            st.latex(r"v = f (\vec{d} \cdot \vec{q}) = " + f"{v:.4f}")
            st.latex(r"u + v = " + f"{(u+v):.4f}")
            
            if v < 0.0 or u + v > 1.0:
                st.error("Raio bateu fora da linha V1-V2 do triângulo.")
                st.session_state.status = "Erro"
            else:
                st.success("Impacto vertical (v) e teste final válidos!")
        
        draw_vector(fig, v0, q, '#FF00FF', 'q', is_active=active)
        
        if st.session_state.step >= 5 and (v >= 0.0 and u + v <= 1.0):
            draw_vector(fig, v0 + u_vec, v_vec, '#FFFF00', 'v', is_active=active)

    if st.session_state.step == 6 and abs(a) > eps and (0.0 <= u <= 1.0) and (v >= 0.0 and u + v <= 1.0):
        t = f * np.dot(e2, q)
        intersection_point = p0 + d * t
        
        st.markdown("**6. Calcular a distância do impacto (t)**")
        st.markdown("**t = f * (e2 · q)**")
        st.markdown("Se as variáveis u e v passaram nos testes anteriores, parabéns! O raio atingiu o triângulo. O valor **t** é exatamente a distância que você deve percorrer desde a origem (P0) na direção do raio (d) para encostar no triângulo.")
        st.latex(r"t = f (e_2 \cdot \vec{q}) = " + f"{t:.4f}")
        st.latex(r"P_{impacto} = P_0 + t\vec{d} = " + f"({intersection_point[0]:.2f}, {intersection_point[1]:.2f}, {intersection_point[2]:.2f})")
        
        fig.add_trace(go.Scatter3d(
            x=[intersection_point[0]], y=[intersection_point[1]], z=[intersection_point[2]],
            mode='markers+text', marker=dict(color='yellow', size=8, symbol='diamond'),
            text=["Ponto Final"], textposition="top right", name='Impacto'
        ))

# Renderização do Gráfico 3D na coluna da direita
with plot_col:
    fig.update_layout(
        uirevision='camera_lock', # Garante que a câmera e zoom não resetem
        height=750, 
        scene=dict(
            xaxis=dict(range=[-5, 5], backgroundcolor="rgb(20, 20, 20)", gridcolor="gray", showbackground=True),
            yaxis=dict(range=[-5, 5], backgroundcolor="rgb(20, 20, 20)", gridcolor="gray", showbackground=True),
            zaxis=dict(range=[-3, 5], backgroundcolor="rgb(20, 20, 20)", gridcolor="gray", showbackground=True),
            aspectmode='cube'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font=dict(color="white")), # Fonte da legenda branca
        paper_bgcolor="black"
    )
    # A remoção de parâmetros extras de UI no plotly_chart também ajuda a estabilizar o uirevision
    st.plotly_chart(fig, use_container_width=True)
