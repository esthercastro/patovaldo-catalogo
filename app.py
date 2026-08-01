import streamlit as st
import os
import re
import csv
import io
import requests
from urllib.parse import quote
from pathlib import Path

# ================== CONFIGURAÇÕES GERAIS ==================
NUMERO_WHATSAPP = "553484012444"
LOGO_PATH = "assets/logo.png"
IMAGEM_FALLBACK = "https://placehold.co/300x300/f0f0f0/999999?text=Sem+Imagem"

# Busca dinâmica de assets (Mapa de entregas / Zonas)
PASTA_PROJETO = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
PASTA_ASSETS = PASTA_PROJETO / "assets"


def buscar_imagem(nome_base: str) -> Path | None:
    if not PASTA_ASSETS.exists():
        return None
    extensoes = [".png", ".jpg", ".jpeg", ".webp", ".PNG", ".JPG", ".JPEG"]
    for ext in extensoes:
        caminho_teste = PASTA_ASSETS / f"{nome_base}{ext}"
        if caminho_teste.exists():
            return caminho_teste
    for arquivo in PASTA_ASSETS.iterdir():
        if arquivo.stem.lower() == nome_base.lower():
            return arquivo
    return None


CAMINHO_MAPA = buscar_imagem("mapa_zonas")

# --- Catálogo (Google Sheets) ---
GOOGLE_SHEET_ID = "1AhD1Mw0PyZ5mvZouEKkofhHovP4d4biOnXQhgLkJOWQ"
GOOGLE_SHEET_GID = "0"
GOOGLE_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid={GOOGLE_SHEET_GID}"
)
CSV_LOCAL_FALLBACK = "produtos.csv"
ORDEM_CATEGORIAS_PREFERIDA = ["Bebidas", "Guloseimas", "Diversos"]

st.set_page_config(
    page_title=" Patovaldo Distribuidora",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOMIZADO UNIFICADO ---
custom_css = """
<style>
    :root {
        --azul: #183B5E;
        --azul-escuro: #10253C;
        --dourado: #E9B83F;
        --verde-whatsapp: #25D366;
    }

    footer {visibility: hidden;}
    [data-testid="stAppDeployButton"] {display: none;}

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Estilo da Barra Lateral (Carrinho Escuro do 2º Código) */
    section[data-testid="stSidebar"] {
        background-color: var(--azul-escuro) !important;
    }

    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #183B5E;
        margin-bottom: 0.2rem;
    }
    .header-sub {
        font-size: 1rem;
        color: #4A5568;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }

    /* Barra de Pesquisa */
    div[data-baseweb="input"] {
        border: 1px solid #CBD5E0 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"]:focus-within {
        border: 1px solid #183B5E !important;
    }

    /* Botões de Categoria */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"],
    div[data-testid="stHorizontalBlock"] button {
        background-color: #FFFFFF !important;
        color: #183B5E !important;
        border: 1px solid #183B5E !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background-color: #183B5E !important;
        color: #FFFFFF !important;
        border: 1px solid #183B5E !important;
    }

    /* Cards de Produtos */
    .product-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    .product-img {
        width: 100%;
        height: 160px;
        object-fit: contain;
        margin-bottom: 8px;
        background: #FAFAFA;
        border-radius: 6px;
    }
    .product-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #2D3748;
        margin: 2px 0 !important;
        min-height: 2.8em;
        line-height: 1.2;
    }
    .product-info {
        font-size: 0.8rem;
        color: #718096;
        margin: 1px 0 !important;
    }
    .min-order {
        color: #1B44BF !important;
        font-weight: 700;
        font-size: 0.8rem;
        margin: 2px 0 !important;
    }
    .product-price {
        font-size: 1.1rem;
        font-weight: 800;
        color: #1A202C;
        margin: 4px 0 !important;
    }

    /* Botão 'Adicionar' Verde */
    div[class*="st-key-add_"] button[kind="secondary"],
    div[class*="st-key-add_"] button {
        background-color: #28A745 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        width: 100%;
    }
    div[class*="st-key-add_"] button:hover {
        background-color: #218838 !important;
        color: #FFFFFF !important;
    }

    /* Itens no Carrinho (Adaptação para o tema escuro da Sidebar) */
    .cart-item {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        padding-bottom: 8px;
    }
    .cart-img {
        width: 42px;
        height: 42px;
        object-fit: contain;
        border-radius: 4px;
        background: #fff;
    }
    .item-carrinho-titulo {
        color: #ffffff;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .item-carrinho-subtotal {
        color: var(--dourado);
        font-weight: 700;
        font-size: 0.85rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}
if 'categoria_ativa' not in st.session_state:
    st.session_state.categoria_ativa = "Todos"


# ================== CARREGAMENTO DO CATÁLOGO ==================
def gerar_id(categoria, nome):
    base = f"{categoria}_{nome}".lower()
    return re.sub(r"[^a-z0-9]+", "_", base).strip("_")


def parse_preco(valor):
    texto = str(valor).strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def parse_descricao(descricao):
    partes = [p.strip() for p in str(descricao).split("|")]
    medida = partes[0] if partes and partes[0] else ""
    minimo = partes[1] if len(partes) > 1 else ""
    return medida, minimo


def linhas_para_produtos(csv_texto):
    produtos_lidos = []
    leitor = csv.DictReader(io.StringIO(csv_texto))
    for linha in leitor:
        nome = (linha.get("produto") or "").strip()
        if not nome:
            continue
        categoria = (linha.get("categoria") or "").strip().title()
        medida, minimo = parse_descricao(linha.get("descricao", ""))
        produtos_lidos.append({
            "id": gerar_id(categoria, nome),
            "nome": nome,
            "medida": medida,
            "minimo": minimo,
            "preco": parse_preco(linha.get("preco", "0")),
            "categoria": categoria,
            "imagem": (linha.get("foto") or "").strip() or IMAGEM_FALLBACK,
        })
    return produtos_lidos


@st.cache_data(ttl=300, show_spinner="Carregando catálogo de produtos...")
def carregar_produtos():
    try:
        resposta = requests.get(GOOGLE_SHEET_CSV_URL, timeout=10)
        resposta.raise_for_status()
        lidos = linhas_para_produtos(resposta.content.decode("utf-8"))
        if lidos:
            return lidos, "online"
    except Exception:
        pass

    if os.path.exists(CSV_LOCAL_FALLBACK):
        try:
            with open(CSV_LOCAL_FALLBACK, encoding="utf-8") as f:
                lidos = linhas_para_produtos(f.read())
            if lidos:
                return lidos, "local"
        except Exception:
            pass

    return [{
        "id": "exemplo_1", "nome": "PRODUTO DE EXEMPLO", "medida": "1 UN.",
        "minimo": "", "preco": 9.90, "categoria": "Diversos", "imagem": IMAGEM_FALLBACK
    }], "exemplo"


produtos, fonte_catalogo = carregar_produtos()


# --- FUNÇÕES DE AUXÍLIO E RENDERIZAÇÃO ---
def render_product_card(p):
    min_html = f'<div class="min-order">{p["minimo"]}</div>' if p["minimo"] else ""
    card_html = (
        f'<div class="product-card">'
        f'<img src="{p["imagem"]}" class="product-img" '
        f'onerror="this.onerror=null;this.src=\'{IMAGEM_FALLBACK}\';">'
        f'<div class="product-title">{p["nome"]}</div>'
        f'<div class="product-info">{p["medida"]}</div>'
        f'{min_html}'
        f'<div class="product-price">R$ {p["preco"]:.2f}</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_cart_item(item):
    subtotal = item["preco"] * item["qtd"]
    item_html = (
        f'<div class="cart-item">'
        f'<img src="{item["imagem"]}" class="cart-img" '
        f'onerror="this.onerror=null;this.src=\'{IMAGEM_FALLBACK}\';">'
        f'<div>'
        f'<div class="item-carrinho-titulo">{item["nome"]}</div>'
        f'<div class="item-carrinho-subtotal">R$ {item["preco"]:.2f} x {item["qtd"]} = R$ {subtotal:.2f}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(item_html, unsafe_allow_html=True)


# --- CABEÇALHO DA PÁGINA ---
col_logo, col_header = st.columns([1, 4])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=130)
    else:
        st.markdown("### 📦")

with col_header:
    st.markdown('<div class="header-title">PATOVALDO DISTRIBUIDORA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="header-sub">'
        '📦 Bebidas e alimentos para estabelecimentos e festas<br>'
        '🚚 Entrega rápida em Patos de Minas e região<br>'
        '👇 Confira nosso catálogo e faça seu pedido!'
        '</div>',
        unsafe_allow_html=True
    )

with st.expander("⚙️ Opções do catálogo"):
    origem_txt = {"online": "Google Sheets (online)", "local": "Arquivo local produtos.csv",
                  "exemplo": "Produto de exemplo"}[fonte_catalogo]
    st.caption(f"Fonte atual dos produtos: **{origem_txt}** · {len(produtos)} produto(s) carregado(s)")
    if st.button("🔄 Atualizar catálogo agora"):
        st.cache_data.clear()
        st.rerun()

# --- BARRA DE PESQUISA & FILTROS ---
busca = st.text_input("", placeholder="🔍 Ex: Cachaça 51, Chiclete...", label_visibility="collapsed")

categorias_no_catalogo = sorted({p["categoria"] for p in produtos})
categorias = (
        ["Todos"]
        + [c for c in ORDEM_CATEGORIAS_PREFERIDA if c in categorias_no_catalogo]
        + [c for c in categorias_no_catalogo if c not in ORDEM_CATEGORIAS_PREFERIDA]
)

cols_cat = st.columns(len(categorias))
for col, cat in zip(cols_cat, categorias):
    with col:
        btn_type = "primary" if st.session_state.categoria_ativa == cat else "secondary"
        if st.button(cat, use_container_width=True, type=btn_type, key=f"cat_{cat}"):
            st.session_state.categoria_ativa = cat
            st.rerun()

# --- FILTRAGEM E GRADE DE PRODUTOS ---
prod_filtrados = [
    p for p in produtos
    if (st.session_state.categoria_ativa == "Todos" or p["categoria"] == st.session_state.categoria_ativa)
       and (busca.lower() in p["nome"].lower())
]

if not prod_filtrados:
    st.info("Nenhum produto encontrado para essa busca/categoria.")
else:
    cols = st.columns(4)
    for idx, p in enumerate(prod_filtrados):
        with cols[idx % 4]:
            render_product_card(p)

            if st.button("Adicionar", key=f"add_{p['id']}", use_container_width=True):
                if p['id'] in st.session_state.carrinho:
                    st.session_state.carrinho[p['id']]['qtd'] += 1
                else:
                    st.session_state.carrinho[p['id']] = {
                        "nome": p['nome'],
                        "preco": p['preco'],
                        "imagem": p['imagem'],
                        "qtd": 1
                    }
                st.toast(f"✅ {p['nome']} adicionado ao carrinho!", icon="🛒")
                st.rerun()

# ================== BARRA LATERAL (NOVO CARRINHO HÍBRIDO) ==================
with st.sidebar:
    total_itens = sum(item["qtd"] for item in st.session_state.carrinho.values())
    st.markdown(f"<h2 style='color:#ffffff; margin-bottom:10px;'>🛒 Seu Pedido ({total_itens})</h2>",
                unsafe_allow_html=True)

    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio. Adicione produtos do catálogo!")
    else:
        total_subitens = 0.0
        linhas_whatsapp = []

        for item_id, item in list(st.session_state.carrinho.items()):
            subtotal = item['preco'] * item['qtd']
            total_subitens += subtotal
            linhas_whatsapp.append(f"• {item['qtd']}x {item['nome']} (R$ {subtotal:.2f})")

            # Linha divisória fina
            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.15);'>", unsafe_allow_html=True)

            # Card do item com foto
            render_cart_item(item)

            # Controles de Quantidade
            c1, c2, c3 = st.columns([1, 1, 2])
            if c1.button("−", key=f"dec_{item_id}"):
                if item['qtd'] > 1:
                    item['qtd'] -= 1
                else:
                    del st.session_state.carrinho[item_id]
                st.rerun()

            c2.markdown(
                f"<div style='text-align:center; color:#ffffff; font-weight:bold; padding-top:4px;'>{item['qtd']}</div>",
                unsafe_allow_html=True)

            if c3.button("＋", key=f"inc_{item_id}"):
                item['qtd'] += 1
                st.rerun()

        st.markdown("<hr style='margin: 1rem 0; border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # Informações adicionais de entrega (Lógica do 2º Código)
        st.markdown("<h4 style='color:#ffffff; margin-bottom: 5px;'>Informações de Entrega</h4>",
                    unsafe_allow_html=True)
        endereco_cliente = st.text_input(
            "Endereço de entrega (Obrigatório):",
            placeholder="Ex: Rua das Flores, 123",
            label_visibility="collapsed"
        )

        if CAMINHO_MAPA and CAMINHO_MAPA.exists():
            st.image(str(CAMINHO_MAPA), caption="Zonas de Entrega e Taxas")

        st.markdown(f"<h3 style='color:#ffffff; margin-top:15px;'>Total: R$ {total_subitens:.2f} + Taxa</h3>",
                    unsafe_allow_html=True)

        # Construção da Mensagem Formatada
        resumo_whatsapp = "Olá! Gostaria de fazer o seguinte pedido:\n\n"
        resumo_whatsapp += "\n".join(linhas_whatsapp)
        resumo_whatsapp += f"\n\n*Subtotal dos itens:* R$ {total_subitens:.2f}"
        resumo_whatsapp += f"\n*Endereço:* {endereco_cliente if endereco_cliente else 'Não informado'}"
        resumo_whatsapp += "\n\nAguardo confirmação da disponibilidade!"

        link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={quote(resumo_whatsapp)}"

        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        # Botão de WhatsApp estilo "Card" Verde
        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#25D366; color:white; padding:12px; text-align:center; border-radius:8px; font-weight:800; font-size:1rem; margin-bottom:12px;">
                    ✅ Finalizar Pedido no WhatsApp
                </div>
            </a>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Limpar Carrinho", use_container_width=True):
            st.session_state.carrinho = {}
            st.rerun()