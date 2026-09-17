import streamlit as st
import os
import re
import csv
import io
import base64
import requests
from urllib.parse import quote
from pathlib import Path

# ================== CONFIGURAÇÕES GERAIS ==================
NUMERO_WHATSAPP = "553484012444"
IMAGEM_FALLBACK = "https://placehold.co/300x300/f8fafc/94a3b8?text=Sem+Foto"

# Localização de pastas e assets
PASTA_PROJETO = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
PASTA_ASSETS = PASTA_PROJETO / "assets"


def buscar_logo() -> str:
    candidatos = [
        PASTA_PROJETO / "logo.png",
        Path("logo.png"),
        PASTA_ASSETS / "logo.png",
        Path("assets/logo.png")
    ]
    for c in candidatos:
        if c.exists():
            return str(c)
    return "logo.png"


LOGO_PATH = buscar_logo()


def carregar_logo_b64() -> str:
    try:
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        pass
    return ""


LOGO_B64 = carregar_logo_b64()


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
    page_title="PatoValdo Distribuidora | Catálogo Online",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== SEO & META TAGS / JSON-LD ==================
seo_html = """
<head>
    <meta name="description" content="PatoValdo Distribuidora em Patos de Minas e região. Bebidas, alimentos, guloseimas e atacado para comércios, festas e eventos com pronta-entrega. Faça seu pedido online!">
    <meta name="keywords" content="Patos de Minas, distribuidora, bebidas, guloseimas, atacado, cerveja, refrigerante, doces, entrega rápida, PatoValdo">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WholesaleStore",
      "name": "PatoValdo Distribuidora",
      "description": "Distribuidora de bebidas e guloseimas no atacado e varejo em Patos de Minas e região.",
      "telephone": "+553484012444",
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "Patos de Minas",
        "addressRegion": "MG",
        "addressCountry": "BR"
      },
      "currenciesAccepted": "BRL",
      "paymentAccepted": "Dinheiro, PIX, Cartão",
      "priceRange": "$$"
    }
    </script>
</head>
"""
st.markdown(seo_html, unsafe_allow_html=True)

# ================== CSS CUSTOMIZADO RESPONSIVO (DESKTOP & MOBILE) ==================
custom_css = """
<style>
    /* Variáveis Globais de Cores e Tipografia */
    :root {
        --azul-institucional: #183B5E;
        --azul-selecionado: #1E3A8A;
        --azul-escuro: #0f253c;
        --azul-claro: #f0f6fc;
        --azul-borda: #cbd5e1;
        --cinza-inativo: #F1F5F9;
        --verde-whatsapp: #25D366;
        --verde-hover: #20BA5A;
        --verde-botao: #16a34a;
        --verde-botao-hover: #15803d;
        --fundo-pagina: #F8FAFC;
        --card-fundo: #FFFFFF;
        --texto-principal: #1E293B;
        --texto-secundario: #64748B;
        --borda-suave: #E2E8F0;
        --alerta-minimo: #d97706;
        --primary-color: #1E3A8A !important;
    }

    *, *::before, *::after {
        box-sizing: border-box !important;
    }

    /* Ocultar elementos padrão do Streamlit */
    footer {visibility: hidden; display: none !important;}
    #MainMenu {visibility: hidden; display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}

    /* Reduzir faixa em branco no topo */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 1rem !important;
        min-height: 1rem !important;
    }

    /* Fundo geral da aplicação */
    .stApp {
        background-color: var(--fundo-pagina);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Container principal */
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 5rem !important;
        max-width: 1280px;
    }

    /* ================= CABEÇALHO RESPONSIVO ================= */
    .header-container {
        background-color: #FFFFFF;
        border: 1px solid var(--borda-suave);
        border-radius: 12px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }
    .header-brand-row {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .header-logo {
        width: 120px;
        height: auto;
        max-height: 90px;
        object-fit: contain;
        flex-shrink: 0;
    }
    .header-text-block {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .header-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--azul-institucional);
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: -0.5px;
        line-height: 1.15;
    }
    .header-sub {
        font-size: 0.9rem;
        color: var(--texto-secundario);
        margin: 0.2rem 0 0.35rem 0 !important;
        line-height: 1.35;
    }
    .header-tag {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        gap: 6px;
        background-color: #EFF6FF;
        color: #1D4ED8;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        border: 1px solid #DBEAFE;
    }

    /* Barra de Pesquisa */
    div[data-baseweb="input"] {
        border-radius: 10px !important;
        border: 1px solid var(--azul-borda) !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: var(--azul-selecionado) !important;
        box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.15) !important;
    }

    /* ================= FILTROS DE CATEGORIA (LINHA ÚNICA HORIZONTAL) ================= */
    div[data-testid="stPills"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        gap: 8px !important;
        margin-top: 0.25rem !important;
        margin-bottom: 0.75rem !important;
        padding: 2px 2px 6px 2px !important;
    }
    div[data-testid="stPills"]::-webkit-scrollbar {
        display: none !important;
    }
    div[data-testid="stPills"] button {
        flex: 0 0 auto !important;
        white-space: nowrap !important;
        background-color: var(--cinza-inativo) !important;
        color: var(--texto-principal) !important;
        border: 1px solid var(--borda-suave) !important;
        border-radius: 20px !important;
        padding: 6px 16px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        outline: none !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stPills"] button:hover {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    /* Estado Selecionado: #1E3A8A, sem borda vermelha/rosa */
    div[data-testid="stPills"] button[aria-selected="true"],
    div[data-testid="stPills"] button[data-checked="true"] {
        background-color: var(--azul-selecionado) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--azul-selecionado) !important;
        box-shadow: 0 2px 4px rgba(30, 58, 138, 0.25) !important;
    }
    div[data-testid="stPills"] button:focus,
    div[data-testid="stPills"] button:focus-visible,
    div[data-testid="stPills"] button:active {
        outline: none !important;
        box-shadow: none !important;
        border-color: var(--azul-selecionado) !important;
    }

    /* Fallback para botões horizontais */
    div[data-testid="stHorizontalBlock"]:has(button[key*="cat_"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        gap: 8px !important;
        padding: 2px 2px 6px 2px !important;
        margin-bottom: 0.75rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="cat_"])::-webkit-scrollbar {
        display: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="cat_"]) > div {
        flex: 0 0 auto !important;
        min-width: auto !important;
        width: auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="cat_"]) button {
        white-space: nowrap !important;
        background-color: var(--cinza-inativo) !important;
        color: var(--texto-principal) !important;
        border: 1px solid var(--borda-suave) !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 6px 16px !important;
        box-shadow: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="cat_"]) button[kind="primary"] {
        background-color: var(--azul-selecionado) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--azul-selecionado) !important;
    }

    /* ================= CARD DE PRODUTO ================= */
    .product-card {
        background-color: #FFFFFF;
        border: 1px solid var(--borda-suave);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }

    /* CONTAINER PADRONIZADO DA IMAGEM */
    .product-img-container {
        width: 100%;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #F8FAFC;
        border-radius: 8px;
        margin-bottom: 8px;
        padding: 8px;
        box-sizing: border-box;
        overflow: hidden;
    }
    .product-img {
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
        object-fit: contain;
        display: block;
        transition: transform 0.25s ease;
    }
    .product-card:hover .product-img {
        transform: scale(1.04);
    }

    /* Detalhes do Produto */
    .product-category-tag {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 700;
        color: var(--azul-institucional);
        background-color: #F0F6FC;
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 3px;
    }
    .product-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: var(--texto-principal);
        margin: 2px 0 3px 0 !important;
        min-height: 2.6em;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .product-info {
        font-size: 0.78rem;
        color: var(--texto-secundario);
        margin: 0 0 3px 0 !important;
        font-weight: 500;
    }
    .min-order {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        font-size: 0.72rem;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #FDE68A;
        margin-bottom: 4px;
    }
    .product-price {
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--azul-institucional);
        margin: 4px 0 0 0 !important;
    }

    /* Botão 'Adicionar' Padronizado */
    div[class*="st-key-add_"] button,
    div[class*="st-key-m_add_"] button {
        background-color: var(--verde-botao) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        height: 44px !important;
        min-height: 44px !important;
        padding: 0 1rem !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(22, 163, 74, 0.2) !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[class*="st-key-add_"] button:hover,
    div[class*="st-key-m_add_"] button:hover {
        background-color: var(--verde-botao-hover) !important;
        box-shadow: 0 4px 8px rgba(22, 163, 74, 0.3) !important;
        transform: translateY(-1px);
    }

    /* ================= SIDEBAR (DESKTOP) ================= */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--borda-suave);
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    .sidebar-header {
        background: linear-gradient(135deg, var(--azul-institucional) 0%, var(--azul-escuro) 100%);
        color: #FFFFFF;
        padding: 12px 14px;
        border-radius: 10px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(24, 59, 94, 0.15);
    }
    .sidebar-header h2 {
        color: #FFFFFF !important;
        font-size: 1.25rem !important;
        margin: 0 !important;
        font-weight: 800;
    }
    .sidebar-header p {
        color: #E2E8F0;
        font-size: 0.8rem;
        margin: 2px 0 0 0;
    }

    /* Card de Item no Carrinho - Limpo sem fórmula matemática */
    .cart-card {
        background: #F8FAFC;
        border: 1px solid var(--borda-suave);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 8px;
    }
    .cart-item-flex {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .cart-img {
        width: 44px;
        height: 44px;
        object-fit: contain;
        border-radius: 6px;
        background: #FFFFFF;
        border: 1px solid var(--borda-suave);
        padding: 2px;
        flex-shrink: 0;
    }
    .item-carrinho-titulo {
        color: var(--texto-principal);
        font-weight: 700;
        font-size: 0.86rem;
        line-height: 1.2;
    }
    .item-carrinho-subtotal {
        color: var(--azul-institucional);
        font-weight: 800;
        font-size: 0.92rem;
        margin-top: 2px;
    }

    /* Botões de quantidade da sidebar alinhados */
    div[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    /* Botão WhatsApp Sidebar */
    .btn-whatsapp {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: var(--verde-whatsapp);
        color: #FFFFFF !important;
        text-align: center;
        padding: 13px 16px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1rem;
        text-decoration: none !important;
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
        transition: all 0.2s ease;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    .btn-whatsapp:hover {
        background-color: var(--verde-hover);
        box-shadow: 0 6px 16px rgba(37, 211, 102, 0.4);
        transform: translateY(-1px);
        color: #FFFFFF !important;
    }

    /* ================= DESKTOP (TELAS ACIMA DE 768PX) ================= */
    @media (min-width: 769px) {
        /* Barra móvel oculta no Desktop */
        .mobile-floating-bar {
            display: none !important;
        }
    }

    /* ================= MOBILE (TELAS ATÉ 768PX) ================= */
    @media (max-width: 768px) {
        /* Ocultar sidebar no mobile */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }

        /* Espaçamento superior e inferior seguro */
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.5rem !important;
            padding-bottom: 105px !important;
            padding-bottom: calc(105px + env(safe-area-inset-bottom, 0px)) !important;
        }

        /* Cabeçalho Compacto Mobile */
        .header-container {
            padding: 0.5rem 0.75rem !important;
            margin-bottom: 0.45rem !important;
            border-radius: 10px !important;
        }
        .header-brand-row {
            gap: 10px !important;
        }
        .header-logo {
            width: 68px !important; /* 65px - 70px */
            max-height: 68px !important;
        }
        .header-title {
            font-size: 1.15rem !important;
            line-height: 1.15 !important;
        }
        .header-sub {
            font-size: 0.76rem !important;
            margin: 0.15rem 0 0.25rem 0 !important;
            line-height: 1.25 !important;
        }
        .header-tag {
            font-size: 0.68rem !important;
            padding: 2px 7px !important;
        }

        /* Imagens mais compactas no mobile para visualização ágil */
        .product-img-container {
            height: 140px !important;
            padding: 6px !important;
        }
        .product-title {
            font-size: 0.84rem !important;
            min-height: 2.4em !important;
            line-height: 1.25 !important;
        }
        .product-price {
            font-size: 1.05rem !important;
        }
        .product-card {
            padding: 10px !important;
        }

        /* Grade responsiva em 2 colunas no celular */
        div[data-testid="stHorizontalBlock"]:has(.product-card) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.product-card) > div[data-testid="column"] {
            flex: 1 1 calc(50% - 6px) !important;
            min-width: calc(50% - 6px) !important;
            max-width: calc(50% - 6px) !important;
            margin-bottom: 8px !important;
        }

        /* ================= BARRA FIXA DO WHATSAPP (MOBILE) ================= */
        .mobile-floating-bar {
            display: block !important;
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            background-color: #FFFFFF !important;
            border-top: 1px solid var(--borda-suave) !important;
            box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.1) !important;
            z-index: 999999 !important;
            padding: 10px 14px !important;
            padding-bottom: calc(10px + env(safe-area-inset-bottom, 0px)) !important;
            box-sizing: border-box !important;
        }
        .mobile-floating-content {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            max-width: 600px !important;
            margin: 0 auto !important;
            gap: 12px !important;
        }
        .mobile-floating-info {
            display: flex !important;
            flex-direction: column !important;
        }
        .mobile-floating-qtd {
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            color: var(--texto-secundario) !important;
        }
        .mobile-floating-total {
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            color: var(--azul-institucional) !important;
            line-height: 1.2 !important;
        }
        .mobile-floating-btn {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background-color: var(--verde-whatsapp) !important;
            color: #FFFFFF !important;
            padding: 10px 18px !important;
            border-radius: 8px !important;
            font-weight: 800 !important;
            font-size: 0.9rem !important;
            text-decoration: none !important;
            box-shadow: 0 2px 6px rgba(37, 211, 102, 0.3) !important;
            min-height: 44px !important;
            white-space: nowrap !important;
        }
        .mobile-floating-btn:active {
            background-color: var(--verde-hover) !important;
        }
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
def gerar_id(categoria: str, nome: str) -> str:
    base = f"{categoria}_{nome}".lower()
    return re.sub(r"[^a-z0-9]+", "_", base).strip("_")


def parse_preco(valor) -> float:
    texto = str(valor).strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def parse_descricao(descricao: str) -> tuple[str, str]:
    partes = [p.strip() for p in str(descricao).split("|")]
    medida = partes[0] if partes and partes[0] else ""
    minimo = partes[1] if len(partes) > 1 else ""
    return medida, minimo


def linhas_para_produtos(csv_texto: str) -> list[dict]:
    produtos_lidos = []
    leitor = csv.DictReader(io.StringIO(csv_texto))
    for linha in leitor:
        nome = (linha.get("produto") or "").strip()
        if not nome:
            continue
        categoria_raw = (linha.get("categoria") or "").strip()
        categoria = categoria_raw.capitalize() if categoria_raw else "Diversos"
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


@st.cache_data(ttl=300, show_spinner=False)
def carregar_produtos():
    try:
        resposta = requests.get(GOOGLE_SHEET_CSV_URL, timeout=10)
        resposta.raise_for_status()
        conteudo = resposta.content.decode("utf-8", errors="replace")
        lidos = linhas_para_produtos(conteudo)
        if lidos:
            return lidos, "online"
    except Exception:
        pass

    if os.path.exists(CSV_LOCAL_FALLBACK):
        try:
            with open(CSV_LOCAL_FALLBACK, encoding="utf-8", errors="replace") as f:
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
def render_product_card(p: dict):
    min_html = f'<div class="min-order">⚠️ {p["minimo"]}</div>' if p.get("minimo") else '<div class="min-order" style="visibility: hidden;">&nbsp;</div>'
    medida_html = f'<div class="product-info">{p["medida"]}</div>' if p.get("medida") else '<div class="product-info">&nbsp;</div>'

    card_html = f"""<div class="product-card">
<div>
<div class="product-img-container">
<img src="{p['imagem']}" class="product-img" loading="lazy" alt="{p['nome']}" onerror="this.onerror=null;this.src='{IMAGEM_FALLBACK}';">
</div>
<div class="product-category-tag">{p['categoria']}</div>
<div class="product-title" title="{p['nome']}">{p['nome']}</div>
{medida_html}
{min_html}
</div>
<div class="product-price">R$ {p['preco']:.2f}</div>
</div>"""

    st.markdown(card_html, unsafe_allow_html=True)

def render_cart_item(item: dict):
    subtotal = item["preco"] * item["qtd"]
    item_html = f"""
    <div class="cart-card">
        <div class="cart-item-flex">
            <img src="{item['imagem']}" class="cart-img"
                 onerror="this.onerror=null;this.src='{IMAGEM_FALLBACK}';">
            <div style="flex-grow:1; min-width:0;">
                <div class="item-carrinho-titulo">{item['nome']}</div>
                <div class="item-carrinho-subtotal">R$ {subtotal:.2f}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(item_html, unsafe_allow_html=True)


# ================== CABEÇALHO DA PÁGINA (COMPACTO E NÍTIDO) ==================
logo_src = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else LOGO_PATH
header_html = f"""
<div class="header-container">
    <div class="header-brand-row">
        <img src="{logo_src}" class="header-logo" alt="PatoValdo Distribuidora">
        <div class="header-text-block">
            <h1 class="header-title">PATOVALDO DISTRIBUIDORA</h1>
            <p class="header-sub">Bebidas e guloseimas no atacado e varejo com pronta-entrega em <b>Patos de Minas e região</b>.</p>
            <div class="header-tag">🚚 Entrega Rápida • Pedido Direto pelo WhatsApp</div>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ================== PESQUISA ==================
busca = st.text_input(
    "Buscar produtos",
    placeholder="🔍 Buscar bebida, guloseima, marca...",
    label_visibility="collapsed"
)

# ================== CATEGORIAS (LINHA ÚNICA HORIZONTAL) ==================
categorias_existentes = sorted({p["categoria"] for p in produtos})
categorias = ["Todos"]
for pref in ORDEM_CATEGORIAS_PREFERIDA:
    if pref.capitalize() in categorias_existentes:
        categorias.append(pref.capitalize())
for c in categorias_existentes:
    if c not in categorias:
        categorias.append(c)

if hasattr(st, "pills"):
    idx_padrao = categorias.index(st.session_state.categoria_ativa) if st.session_state.categoria_ativa in categorias else 0
    cat_selecionada = st.pills(
        "Categorias",
        options=categorias,
        default=categorias[idx_padrao],
        key="pills_categorias",
        label_visibility="collapsed"
    )
    if cat_selecionada and cat_selecionada != st.session_state.categoria_ativa:
        st.session_state.categoria_ativa = cat_selecionada
        st.rerun()
    elif not cat_selecionada and st.session_state.categoria_ativa != "Todos":
        st.session_state.categoria_ativa = "Todos"
        st.rerun()
else:
    cols_cat = st.columns(len(categorias))
    for col, cat in zip(cols_cat, categorias):
        with col:
            tipo_btn = "primary" if st.session_state.categoria_ativa == cat else "secondary"
            if st.button(cat, use_container_width=True, type=tipo_btn, key=f"cat_{cat}"):
                st.session_state.categoria_ativa = cat
                st.rerun()

# ================== FILTRAGEM DOS PRODUTOS ==================
termo_busca = busca.strip().lower()
prod_filtrados = [
    p for p in produtos
    if (st.session_state.categoria_ativa == "Todos" or p["categoria"] == st.session_state.categoria_ativa)
    and (not termo_busca or termo_busca in p["nome"].lower() or termo_busca in p["categoria"].lower())
]

# Totalizadores do Carrinho
total_itens = sum(item["qtd"] for item in st.session_state.carrinho.values())
total_subitens = sum(item["preco"] * item["qtd"] for item in st.session_state.carrinho.values())

# ================== GRADE DE PRODUTOS ==================
if not prod_filtrados:
    st.info(f"Nenhum produto encontrado para a categoria **{st.session_state.categoria_ativa}** ou termo de busca.")
else:
    num_colunas = 4
    cols = st.columns(num_colunas)
    for idx, p in enumerate(prod_filtrados):
        with cols[idx % num_colunas]:
            render_product_card(p)
            
            if st.button("➕ Adicionar", key=f"add_{p['id']}", use_container_width=True):
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

# ================== SIDEBAR (DESKTOP - SEU PEDIDO) ==================
with st.sidebar:
    st.markdown(f"""
        <div class="sidebar-header">
            <h2>🛒 Seu Pedido ({total_itens})</h2>
            <p>Patovaldo Distribuidora</p>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.carrinho:
        st.markdown("""
            <div style="text-align:center; padding: 2rem 1rem; color: #64748B;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🛍️</div>
                <p style="font-size: 0.95rem; font-weight: 600; margin-bottom: 0.2rem;">Seu carrinho está vazio</p>
                <p style="font-size: 0.8rem;">Clique em <b>Adicionar</b> nos produtos para iniciar seu pedido.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        linhas_whatsapp = []

        for item_id, item in list(st.session_state.carrinho.items()):
            subtotal = item['preco'] * item['qtd']
            linhas_whatsapp.append(f"• {item['qtd']}x {item['nome']} (R$ {subtotal:.2f})")

            # Card individual de produto no carrinho
            render_cart_item(item)

            # Controles de quantidade (+, -, remover)
            c1, c2, c3 = st.columns([1, 1, 1])
            if c1.button("−", key=f"dec_{item_id}", use_container_width=True):
                if item['qtd'] > 1:
                    item['qtd'] -= 1
                else:
                    del st.session_state.carrinho[item_id]
                st.rerun()

            c2.markdown(
                f"<div style='text-align:center; color:#1E293B; font-weight:700; padding-top:6px;'>{item['qtd']}</div>",
                unsafe_allow_html=True
            )

            if c3.button("＋", key=f"inc_{item_id}", use_container_width=True):
                item['qtd'] += 1
                st.rerun()

        st.markdown("<hr style='margin: 1rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        # Dados para entrega
        st.markdown("<p style='font-weight:700; color:#1E293B; font-size:0.9rem; margin-bottom:4px;'>📍 Endereço de Entrega (Opcional):</p>", unsafe_allow_html=True)
        endereco_cliente = st.text_input(
            "Endereço de entrega:",
            placeholder="Ex: Rua Major Gote, 1200 - Centro",
            label_visibility="collapsed"
        )

        if CAMINHO_MAPA and CAMINHO_MAPA.exists():
            with st.expander("🗺️ Ver Zonas de Entrega e Taxas"):
                st.image(str(CAMINHO_MAPA), caption="Zonas de Entrega em Patos de Minas", use_container_width=True)

        st.markdown(f"""
            <div style="background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px; margin: 12px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#166534;">Subtotal do Pedido:</span>
                    <span style="font-size:1.25rem; font-weight:800; color:#15803D;">R$ {total_subitens:.2f}</span>
                </div>
                <div style="font-size:0.75rem; color:#166534; margin-top:2px;">* Taxa de entrega calculada via WhatsApp</div>
            </div>
        """, unsafe_allow_html=True)

        # Montagem da mensagem formatada para o WhatsApp
        resumo_whatsapp = "Olá! Gostaria de fazer o seguinte pedido na *Patovaldo Distribuidora*:\n\n"
        resumo_whatsapp += "*ITENS DO PEDIDO:*\n"
        resumo_whatsapp += "\n".join(linhas_whatsapp)
        resumo_whatsapp += f"\n\n*Subtotal dos itens:* R$ {total_subitens:.2f}"
        resumo_whatsapp += f"\n*Endereço de Entrega:* {endereco_cliente.strip() if endereco_cliente.strip() else 'A combinar / Retirada'}"
        resumo_whatsapp += "\n\nPor favor, confirme a disponibilidade e o valor da entrega. Obrigado!"

        link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={quote(resumo_whatsapp)}"

        # Botão de Envio para o WhatsApp
        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" class="btn-whatsapp">
                📲 Finalizar Pedido no WhatsApp
            </a>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Limpar Carrinho", use_container_width=True):
            st.session_state.carrinho = {}
            st.rerun()

# ================== BARRA FIXA DO WHATSAPP (EXCLUSIVA MOBILE) ==================
# Exibida de forma fixa na parte inferior do celular quando há itens no carrinho
if total_itens > 0:
    if 'link_whatsapp' not in locals():
        resumo_padrao = f"Olá! Gostaria de fazer um pedido no valor de R$ {total_subitens:.2f} ({total_itens} itens)."
        link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={quote(resumo_padrao)}"

    texto_qtd = "1 item" if total_itens == 1 else f"{total_itens} itens"
    st.markdown(f"""
        <div class="mobile-floating-bar">
            <div class="mobile-floating-content">
                <div class="mobile-floating-info">
                    <span class="mobile-floating-qtd">🛒 {texto_qtd}</span>
                    <span class="mobile-floating-total">R$ {total_subitens:.2f}</span>
                </div>
                <a href="{link_whatsapp}" target="_blank" class="mobile-floating-btn">
                    Finalizar no WhatsApp ➔
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)