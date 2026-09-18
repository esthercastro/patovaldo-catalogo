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
        PASTA_PROJETO / "logo_destaque.png",
        Path("logo_destaque.png"),
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
    """Carrega a logo, aplicando auto-trimming das margens brancas para que o mascote e texto fiquem grandes e nítidos."""
    candidatos = [
        PASTA_PROJETO / "logo_destaque.png",
        Path("logo_destaque.png"),
        PASTA_PROJETO / "logo.png",
        Path("logo.png"),
    ]
    for c in candidatos:
        if c.exists():
            try:
                from PIL import Image, ImageChops
                im = Image.open(c)
                # Remove o excesso de borda branca da imagem original (1600x1600)
                bg = Image.new("RGB", im.size, (255, 255, 255))
                diff = ImageChops.difference(im.convert("RGB"), bg)
                bbox = diff.getbbox()
                if bbox:
                    pad = 18
                    b = (
                        max(0, bbox[0] - pad),
                        max(0, bbox[1] - pad),
                        min(im.size[0], bbox[2] + pad),
                        min(im.size[1], bbox[3] + pad),
                    )
                    im = im.crop(b)
                im.thumbnail((450, 450), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, format="PNG", optimize=True)
                return base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception:
                with open(c, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
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
    <meta name="description" content="PatoValdo Distribuidora de Bebidas e Doces em Patos de Minas. Atacado para comércios, festas e eventos com pronta-entrega. Faça seu pedido online por WhatsApp!">
    <meta name="keywords" content="Patos de Minas, distribuidora, bebidas, doces, guloseimas, atacado, entrega rápida, Patovaldo">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WholesaleStore",
      "name": "PatoValdo Distribuidora",
      "description": "Nossas bebidas e doces estão presentes nas melhores festas de Patos de Minas e região! A Patovaldo combina atendimento ágil e variedade de estoque para abastecer o seu comércio.",
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
    /* Rolagem suave para links de âncora */
    html {
        scroll-behavior: smooth;
    }

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

    /* ================= CABEÇALHO HERO PREMIUM & CHAMATIVO ================= */
    .header-container {
        background: linear-gradient(135deg, #0d2238 0%, #183B5E 55%, #1f4e7d 100%);
        border-radius: 16px;
        padding: 1.25rem 1.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(16, 37, 60, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.12);
        position: relative;
        overflow: hidden;
    }
    /* Efeito de luz dourada sutil */
    .header-container::after {
        content: '';
        position: absolute;
        top: -60px;
        right: -60px;
        width: 190px;
        height: 190px;
        background: radial-gradient(circle, rgba(233, 184, 63, 0.22) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .header-brand-row {
        display: flex;
        align-items: center;
        gap: 20px;
        position: relative;
        z-index: 1;
    }
    /* Card da Logo em Destaque (ampliada e nítida) */
    .header-logo-badge {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.22);
        flex-shrink: 0;
        width: 145px;
        height: 110px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .header-logo-badge:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.28);
    }
    .header-logo {
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
        object-fit: contain;
        display: block;
    }
    .header-text-block {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 3px;
    }
    .header-badge-distribuidora {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        background: rgba(233, 184, 63, 0.18);
        color: #FCE588;
        border: 1px solid rgba(233, 184, 63, 0.45);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 2px;
    }
    .header-title {
        font-size: 1.95rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0 !important;
        padding: 0 !important;
        letter-spacing: -0.5px;
        line-height: 1.15;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .header-sub {
        font-size: 0.92rem;
        color: #E2E8F0 !important;
        margin: 0.15rem 0 0.45rem 0 !important;
        line-height: 1.4;
        max-width: 820px;
    }
    .header-tags-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
    }
    .header-tag-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(255, 255, 255, 0.14);
        backdrop-filter: blur(4px);
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        border: 1px solid rgba(255, 255, 255, 0.22);
    }
    .header-tag-destaque {
        background: linear-gradient(135deg, #25D366 0%, #15803D 100%) !important;
        border: 1px solid rgba(37, 211, 102, 0.6) !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(37, 211, 102, 0.35);
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

    /* Botões de quantidade alinhados */
    div[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"],
    .st-key-carrinho_mobile_expander div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    /* Botão WhatsApp */
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
        /* Barra móvel e expander mobile ocultos no Desktop */
        .mobile-floating-bar,
        .st-key-carrinho_mobile_expander,
        .mobile-cart-marker {
            display: none !important;
        }
    }

    /* ================= MOBILE (TELAS ATÉ 768PX) ================= */
    @media (max-width: 768px) {
        /* Ocultar sidebar no mobile para dar foco ao expander in-page e barra flutuante */
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
            padding-bottom: 115px !important;
            padding-bottom: calc(115px + env(safe-area-inset-bottom, 0px)) !important;
        }

        /* Cabeçalho Compacto e Marcante Mobile */
        .header-container {
            padding: 0.75rem 0.9rem !important;
            margin-bottom: 0.55rem !important;
            border-radius: 12px !important;
        }
        .header-brand-row {
            gap: 12px !important;
            align-items: center !important;
        }
        .header-logo-badge {
            width: 85px !important;
            height: 75px !important;
            padding: 4px 6px !important;
            border-radius: 10px !important;
        }
        .header-title {
            font-size: 1.22rem !important;
            line-height: 1.15 !important;
        }
        .header-badge-distribuidora {
            font-size: 0.62rem !important;
            padding: 1px 6px !important;
        }
        .header-sub {
            font-size: 0.75rem !important;
            line-height: 1.25 !important;
            margin: 0.1rem 0 0.3rem 0 !important;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .header-tags-row {
            gap: 5px !important;
        }
        .header-tag-pill {
            font-size: 0.68rem !important;
            padding: 2px 7px !important;
        }

        /* ================= ESTILIZAÇÃO DO EXPANDER DE CARRINHO MOBILE ================= */
        .st-key-carrinho_mobile_expander {
            background-color: #FFFFFF !important;
            border: 2px solid var(--azul-institucional) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 14px rgba(24, 59, 94, 0.12) !important;
            margin-top: 0.4rem !important;
            margin-bottom: 0.85rem !important;
            overflow: hidden !important;
        }
        .st-key-carrinho_mobile_expander details {
            border-radius: 10px !important;
        }
        .st-key-carrinho_mobile_expander summary {
            background: linear-gradient(135deg, #183B5E 0%, #0d2238 100%) !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 0.95rem !important;
            padding: 11px 14px !important;
            border-radius: 10px !important;
        }
        .st-key-carrinho_mobile_expander summary:hover {
            background: linear-gradient(135deg, #1f4e7d 0%, #183B5E 100%) !important;
        }
        .st-key-carrinho_mobile_expander summary span {
            color: #FFFFFF !important;
        }
        .st-key-carrinho_mobile_expander summary svg {
            fill: #FFFFFF !important;
        }

        /* Imagens compactas e centradas */
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

        /* ================= BARRA FIXA DO WHATSAPP COM BOTÃO DE VER CARRINHO (MOBILE) ================= */
        .mobile-floating-bar {
            display: block !important;
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            background-color: #FFFFFF !important;
            border-top: 1px solid var(--borda-suave) !important;
            box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.12) !important;
            z-index: 999999 !important;
            padding: 8px 12px !important;
            padding-bottom: calc(8px + env(safe-area-inset-bottom, 0px)) !important;
            box-sizing: border-box !important;
        }
        .mobile-floating-content {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            max-width: 600px !important;
            margin: 0 auto !important;
            gap: 8px !important;
        }
        .mobile-floating-info-link {
            display: flex !important;
            flex-direction: column !important;
            text-decoration: none !important;
            flex-shrink: 0 !important;
        }
        .mobile-floating-qtd {
            font-size: 0.74rem !important;
            font-weight: 600 !important;
            color: var(--texto-secundario) !important;
        }
        .mobile-floating-total {
            font-size: 1.08rem !important;
            font-weight: 800 !important;
            color: var(--azul-institucional) !important;
            line-height: 1.15 !important;
        }
        .mobile-floating-btn-cart {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background-color: #F1F5F9 !important;
            color: var(--azul-institucional) !important;
            border: 1.5px solid var(--azul-institucional) !important;
            padding: 8px 10px !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 0.8rem !important;
            text-decoration: none !important;
            min-height: 40px !important;
            white-space: nowrap !important;
            transition: all 0.15s ease !important;
        }
        .mobile-floating-btn-cart:active {
            background-color: #E2E8F0 !important;
        }
        .mobile-floating-btn {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background-color: var(--verde-whatsapp) !important;
            color: #FFFFFF !important;
            padding: 8px 14px !important;
            border-radius: 8px !important;
            font-weight: 800 !important;
            font-size: 0.86rem !important;
            text-decoration: none !important;
            box-shadow: 0 2px 6px rgba(37, 211, 102, 0.3) !important;
            min-height: 40px !important;
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
if 'endereco' not in st.session_state:
    st.session_state.endereco = ""
if 'cupom' not in st.session_state:
    st.session_state.cupom = ""


# Callbacks para sincronização bidirecional de campos entre Mobile e Sidebar
def sync_mobile_inputs():
    val_end = st.session_state.get("m_endereco_input", "")
    val_cup = st.session_state.get("m_cupom_input", "")
    st.session_state.endereco = val_end
    st.session_state.cupom = val_cup
    st.session_state.s_endereco_input = val_end
    st.session_state.s_cupom_input = val_cup


def sync_sidebar_inputs():
    val_end = st.session_state.get("s_endereco_input", "")
    val_cup = st.session_state.get("s_cupom_input", "")
    st.session_state.endereco = val_end
    st.session_state.cupom = val_cup
    st.session_state.m_endereco_input = val_end
    st.session_state.m_cupom_input = val_cup


if "m_endereco_input" not in st.session_state:
    st.session_state.m_endereco_input = st.session_state.endereco
if "s_endereco_input" not in st.session_state:
    st.session_state.s_endereco_input = st.session_state.endereco
if "m_cupom_input" not in st.session_state:
    st.session_state.m_cupom_input = st.session_state.cupom
if "s_cupom_input" not in st.session_state:
    st.session_state.s_cupom_input = st.session_state.cupom


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
    # Suporte flexível automático para separadores de vírgula ou ponto-e-vírgula
    primeira_linha = csv_texto.splitlines()[0] if csv_texto.splitlines() else ""
    delimitador = ";" if ";" in primeira_linha else ","
    leitor = csv.DictReader(io.StringIO(csv_texto), delimiter=delimitador)
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


def gerar_link_whatsapp(carrinho: dict, total_sub: float, endereco: str, cupom: str) -> str:
    linhas = []
    for item in carrinho.values():
        sub = item['preco'] * item['qtd']
        linhas.append(f"• {item['qtd']}x {item['nome']} (R$ {sub:.2f})")

    end_formatado = endereco.strip() if endereco and endereco.strip() else "A combinar / Retirada"

    msg = "Olá! Gostaria de fazer o seguinte pedido na *Patovaldo Distribuidora*:\n\n"
    msg += "*ITENS DO PEDIDO:*\n"
    msg += "\n".join(linhas)
    msg += f"\n\n*Subtotal dos itens:* R$ {total_sub:.2f}"
    msg += f"\n*Endereço de Entrega:* {end_formatado}"
    if cupom and cupom.strip():
        msg += f"\n*Cupom:* {cupom.strip().upper()}"
    msg += "\n\nAguardo confirmação da disponibilidade e taxa de entrega!"

    return f"https://wa.me/{NUMERO_WHATSAPP}?text={quote(msg)}"


# ================== CABEÇALHO HERO PREMIUM & CHAMATIVO ==================
logo_src = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else LOGO_PATH
header_html = f"""
<div class="header-container">
    <div class="header-brand-row">
        <div class="header-logo-badge">
            <img src="{logo_src}" class="header-logo" alt="PatoValdo Distribuidora">
        </div>
        <div class="header-text-block">
            <h1 class="header-title">CATÁLOGO: PATOVALDO DISTRIBUIDORA</h1>
            <p class="header-sub">Variedade em bebidas e doces para abastecer seu comércio e transformar seus eventos em Patos de Minas.</p>
            <div class="header-tags-row">
                <div class="header-tag-pill"> 👇 Escolha seus produtos!</div>
            </div>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ================== PESQUISA ==================
busca = st.text_input(
    "Buscar produtos",
    placeholder="🔍 Buscar bebida, doce, marca...",
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

# ================== CARRINHO EXPANSÍVEL (EXCLUSIVO MOBILE) ==================
# Exibido no topo da página no celular quando há produtos no carrinho
if total_itens > 0:
    st.markdown('<div id="carrinho-mobile" class="mobile-cart-marker"></div>', unsafe_allow_html=True)
    with st.expander(
        f"🛒 Ver / Concluir Pedido ({total_itens} {'item' if total_itens == 1 else 'itens'} • R$ {total_subitens:.2f})",
        expanded=False,
        key="carrinho_mobile_expander"
    ):
        st.markdown("<h4 style='color:#183B5E; margin:0 0 10px 0; font-size:1.05rem; font-weight:800;'>🛍️ Itens no seu Carrinho</h4>", unsafe_allow_html=True)

        for item_id, item in list(st.session_state.carrinho.items()):
            render_cart_item(item)

            m1, m2, m3 = st.columns([1, 1, 1])
            if m1.button("−", key=f"m_dec_{item_id}", use_container_width=True):
                if item['qtd'] > 1:
                    item['qtd'] -= 1
                else:
                    del st.session_state.carrinho[item_id]
                st.rerun()

            m2.markdown(
                f"<div style='text-align:center; color:#1E293B; font-weight:700; padding-top:6px;'>{item['qtd']}</div>",
                unsafe_allow_html=True
            )

            if m3.button("＋", key=f"m_inc_{item_id}", use_container_width=True):
                item['qtd'] += 1
                st.rerun()

        st.markdown("<hr style='margin: 1rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        # Dados para entrega
        st.markdown("<p style='font-weight:700; color:#1E293B; font-size:0.9rem; margin-bottom:4px;'>📍 Endereço de Entrega (Opcional):</p>", unsafe_allow_html=True)
        st.text_input(
            "Endereço de entrega:",
            placeholder="Ex: Rua Major Gote, 1200 - Centro",
            label_visibility="collapsed",
            key="m_endereco_input",
            on_change=sync_mobile_inputs
        )

        if CAMINHO_MAPA and CAMINHO_MAPA.exists():
            with st.expander("🗺️ Ver Zonas de Entrega e Taxas", key="m_exp_zonas"):
                st.image(str(CAMINHO_MAPA), caption="Zonas de Entrega em Patos de Minas", use_container_width=True)

        # Campo Cupom (Facultativo / Opcional)
        st.markdown("<p style='font-weight:700; color:#1E293B; font-size:0.9rem; margin-top:8px; margin-bottom:4px;'>🏷️ Cupom (Opcional):</p>", unsafe_allow_html=True)
        st.text_input(
            "Cupom:",
            placeholder="Ex: PATOVALDO10",
            label_visibility="collapsed",
            key="m_cupom_input",
            on_change=sync_mobile_inputs
        )

        st.markdown(f"""
            <div style="background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px; margin: 12px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#166534;">Subtotal do Pedido:</span>
                    <span style="font-size:1.25rem; font-weight:800; color:#15803D;">R$ {total_subitens:.2f}</span>
                </div>
                <div style="font-size:0.75rem; color:#166534; margin-top:2px;">* Taxa de entrega calculada via WhatsApp</div>
            </div>
        """, unsafe_allow_html=True)

        link_zap_mobile = gerar_link_whatsapp(
            st.session_state.carrinho, total_subitens, st.session_state.endereco, st.session_state.cupom
        )

        st.markdown(f"""
            <a href="{link_zap_mobile}" target="_blank" class="btn-whatsapp">
                📲 Finalizar Pedido no WhatsApp
            </a>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Limpar Carrinho", key="m_limpar_carrinho", use_container_width=True):
            st.session_state.carrinho = {}
            st.rerun()

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
        for item_id, item in list(st.session_state.carrinho.items()):
            # Card individual de produto no carrinho
            render_cart_item(item)

            # Controles de quantidade (+, -, remover)
            c1, c2, c3 = st.columns([1, 1, 1])
            if c1.button("−", key=f"s_dec_{item_id}", use_container_width=True):
                if item['qtd'] > 1:
                    item['qtd'] -= 1
                else:
                    del st.session_state.carrinho[item_id]
                st.rerun()

            c2.markdown(
                f"<div style='text-align:center; color:#1E293B; font-weight:700; padding-top:6px;'>{item['qtd']}</div>",
                unsafe_allow_html=True
            )

            if c3.button("＋", key=f"s_inc_{item_id}", use_container_width=True):
                item['qtd'] += 1
                st.rerun()

        st.markdown("<hr style='margin: 1rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        # Dados para entrega
        st.markdown("<p style='font-weight:700; color:#1E293B; font-size:0.9rem; margin-bottom:4px;'>📍 Endereço de Entrega (Opcional):</p>", unsafe_allow_html=True)
        st.text_input(
            "Endereço de entrega:",
            placeholder="Ex: Rua Major Gote, 1200 - Centro",
            label_visibility="collapsed",
            key="s_endereco_input",
            on_change=sync_sidebar_inputs
        )

        if CAMINHO_MAPA and CAMINHO_MAPA.exists():
            with st.expander("🗺️ Ver Zonas de Entrega e Taxas", key="s_exp_zonas"):
                st.image(str(CAMINHO_MAPA), caption="Zonas de Entrega em Patos de Minas", use_container_width=True)

        # Campo Cupom (Facultativo / Opcional)
        st.markdown("<p style='font-weight:700; color:#1E293B; font-size:0.9rem; margin-top:8px; margin-bottom:4px;'>🏷️ Cupom (Opcional):</p>", unsafe_allow_html=True)
        st.text_input(
            "Cupom:",
            placeholder="Ex: PATOVALDO10",
            label_visibility="collapsed",
            key="s_cupom_input",
            on_change=sync_sidebar_inputs
        )

        st.markdown(f"""
            <div style="background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px; margin: 12px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; color:#166534;">Subtotal do Pedido:</span>
                    <span style="font-size:1.25rem; font-weight:800; color:#15803D;">R$ {total_subitens:.2f}</span>
                </div>
                <div style="font-size:0.75rem; color:#166534; margin-top:2px;">* Taxa de entrega calculada via WhatsApp</div>
            </div>
        """, unsafe_allow_html=True)

        link_whatsapp = gerar_link_whatsapp(
            st.session_state.carrinho, total_subitens, st.session_state.endereco, st.session_state.cupom
        )

        # Botão de Envio para o WhatsApp
        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" class="btn-whatsapp">
                📲 Finalizar Pedido no WhatsApp
            </a>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Limpar Carrinho", key="s_limpar_carrinho", use_container_width=True):
            st.session_state.carrinho = {}
            st.rerun()

# ================== BARRA FIXA DO WHATSAPP COM LINK DO CARRINHO (EXCLUSIVA MOBILE) ==================
# Exibida de forma fixa na parte inferior do celular quando há itens no carrinho
if total_itens > 0:
    link_zap_float = gerar_link_whatsapp(
        st.session_state.carrinho, total_subitens, st.session_state.endereco, st.session_state.cupom
    )
    texto_qtd = "1 item" if total_itens == 1 else f"{total_itens} itens"
    st.markdown(f"""
        <div class="mobile-floating-bar">
            <div class="mobile-floating-content">
                <a href="#carrinho-mobile" class="mobile-floating-info-link" title="Toque para ver os produtos">
                    <span class="mobile-floating-qtd">🛒 {texto_qtd}</span>
                    <span class="mobile-floating-total">R$ {total_subitens:.2f}</span>
                </a>
                <a href="#carrinho-mobile" class="mobile-floating-btn-cart">
                    Ver Pedido 📝
                </a>
                <a href="{link_zap_float}" target="_blank" class="mobile-floating-btn">
                    Pedir no Zap ➔
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)
