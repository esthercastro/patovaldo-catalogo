import streamlit as st
import pandas as pd
import urllib.parse
import requests
from html import escape
import re

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageChops

# ---------------- CONFIGURAÇÕES MOBILE ---------------- #

st.set_page_config(
    page_title="Patovaldo | Catálogo Mobile 📱",
    page_icon="🦆",
    layout="centered",  # Layout centralizado ideal para telemóveis
    initial_sidebar_state="collapsed",  # Começa recolhido no celular
)

NUMERO_WHATSAPP = "+553484012444"
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1AhD1Mw0PyZ5mvZouEKkofhHovP4d4biOnXQhgLkJOWQ/"
    "export?format=csv&gid=0"
)

# Caminhos de arquivos
PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_ASSETS = PASTA_PROJETO / "assets"


def buscar_imagem(nome_base: str) -> Path | None:
    """Procura um arquivo na pasta 'assets' testando várias extensões."""
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


CAMINHO_LOGO = buscar_imagem("logo")
CAMINHO_MAPA = buscar_imagem("mapa_zonas")
CAMINHO_CARRINHO = buscar_imagem("carrinho")

if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}

if "categoria_selecionada" not in st.session_state:
    st.session_state.categoria_selecionada = "TODOS OS PRODUTOS"

# ---------------- ESTILO CSS EXCLUSIVO PARA MOBILE ---------------- #

st.markdown(
    """
<style>
    :root {
        --azul: #183b5e;
        --azul-escuro: #10253c;
        --dourado: #e9b83f;
    }

    .stApp {
        background-color: #f7f9fb;
        color: var(--azul);
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* Cabeçalho compacto */
    .marca-mobile {
        color: var(--azul);
        font-size: 1.3rem;
        font-weight: 850;
        text-align: center;
        margin: 0;
    }

    .subtitulo-mobile {
        color: #475569;
        font-size: 0.8rem;
        text-align: center;
        margin-bottom: 10px;
    }

    /* Campo de Busca Otimizado para Toque */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #183b5e !important;
        font-weight: 600 !important;
        border: 2px solid #183b5e !important;
        border-radius: 8px !important;
        height: 45px !important;
    }

    /* Card de Produto em Fila Única no Celular */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #e1e7ed !important;
        border-radius: 12px;
        padding: 0.6rem;
        margin-bottom: 10px;
    }

    .produto-titulo {
        color: var(--azul);
        font-size: 0.95rem;
        font-weight: 800;
        text-align: center;
        margin-top: 5px;
    }

    .produto-preco {
        color: var(--azul);
        font-size: 1.3rem;
        font-weight: 900;
        text-align: center;
        margin: 5px 0;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--azul-escuro) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- FUNÇÕES ---------------- #

@st.cache_data
def carregar_logo(caminho):
    logo = Image.open(caminho).convert("RGBA")
    margem = 10
    logo_com_margem = Image.new(
        "RGBA",
        (logo.width + margem * 2, logo.height + margem * 2),
        (255, 255, 255, 0),
    )
    logo_com_margem.alpha_composite(logo, (margem, margem))
    return logo_com_margem


def corrigir_link_imagem(link):
    link = str(link).strip()
    if "drive.google.com/file/d/" in link:
        arquivo_id = link.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?export=view&id={arquivo_id}"
    return link


@st.cache_data(ttl=3600)
def preparar_imagem_produto(link):
    largura, altura = 600, 480
    fundo = (248, 251, 254, 255)

    try:
        resposta = requests.get(corrigir_link_imagem(link), timeout=15)
        resposta.raise_for_status()

        imagem_original = Image.open(BytesIO(resposta.content)).convert("RGBA")
        imagem_original.thumbnail((500, 400), Image.Resampling.LANCZOS)

        quadro = Image.new("RGBA", (largura, altura), fundo)
        posicao_x = (largura - imagem_original.width) // 2
        posicao_y = (altura - imagem_original.height) // 2
        quadro.alpha_composite(imagem_original, (posicao_x, posicao_y))

        return quadro.convert("RGB")
    except Exception:
        return Image.new("RGB", (largura, altura), fundo[:3])


@st.cache_data(ttl=300)
def carregar_dados():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.lower()
        df = df.rename(
            columns={
                "categoria": "Categoria",
                "produto": "Produto",
                "preco": "Preço",
                "preço": "Preço",
                "descricao": "Descrição",
                "descrição": "Descrição",
                "foto": "Foto",
            }
        )
        if "Categoria" not in df.columns:
            df["Categoria"] = "DIVERSOS"
        df["Categoria"] = df["Categoria"].fillna("DIVERSOS").astype(str).str.strip().str.upper()

        if "Preço" in df.columns:
            texto_preco = df["Preço"].astype(str).str.replace("R$", "", regex=False).str.strip().str.replace(",", ".",
                                                                                                             regex=False)
            df["Preço"] = pd.to_numeric(texto_preco, errors="coerce")

        return df.dropna(subset=["Produto"])
    except Exception as erro:
        st.error(f"Erro ao carregar dados: {erro}")
        return pd.DataFrame()


def formatar_preco(preco):
    return f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------- CARRINHO ---------------- #

def adicionar_ao_carrinho(nome, preco):
    if pd.isna(preco):
        preco = 0.0
    if nome in st.session_state.carrinho:
        st.session_state.carrinho[nome]["qtd"] += 1
    else:
        st.session_state.carrinho[nome] = {"preco": preco, "qtd": 1}
    st.toast(f"✅ {nome} adicionado!", icon="🛒")


def remover_do_carrinho(nome):
    if nome in st.session_state.carrinho:
        if st.session_state.carrinho[nome]["qtd"] > 1:
            st.session_state.carrinho[nome]["qtd"] -= 1
        else:
            del st.session_state.carrinho[nome]


def esvaziar_carrinho():
    st.session_state.carrinho = {}


def set_categoria(categoria):
    st.session_state.categoria_selecionada = categoria


# ---------------- CABEÇALHO MOBILE ---------------- #

col_logo, col_txt = st.columns([1, 3])
with col_logo:
    if CAMINHO_LOGO and CAMINHO_LOGO.exists():
        st.image(carregar_logo(str(CAMINHO_LOGO)), width=90)
with col_txt:
    st.markdown('<p class="marca-mobile">PATOVALDO DISTRIBUIDORA</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-mobile">📱 Catálogo Mobile Otimizado</p>', unsafe_allow_html=True)

# BARRA LATERAL (CARRINHO MOBILE)
with st.sidebar:
    total_itens = sum(item["qtd"] for item in st.session_state.carrinho.values())
    st.title(f"🛒 Seu Pedido ({total_itens})")

    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio.")
    else:
        total_subitens = 0
        for item, dados in list(st.session_state.carrinho.items()):
            subtotal = dados["qtd"] * dados["preco"]
            total_subitens += subtotal
            st.write(f"**{item}**")

            c_rem, c_qtd, c_add = st.columns([1, 1, 1])
            with c_rem:
                st.button("−", key=f"mob_rem_{item}", on_click=remover_do_carrinho, args=(item,))
            with c_qtd:
                st.write(f"Qtd: **{dados['qtd']}**")
            with c_add:
                st.button("＋", key=f"mob_add_{item}", on_click=adicionar_ao_carrinho, args=(item, dados["preco"]))

            st.caption(f"Subtotal: R$ {formatar_preco(subtotal)}")
            st.divider()

        endereco_cliente = st.text_input("Endereço de entrega:", placeholder="Sua rua e número")
        st.markdown(f"### Total: R$ {formatar_preco(total_subitens)}")

        resumo_whatsapp = "Olá! Gostaria de fazer o seguinte pedido (Mobile):\n\n"
        for item, dados in list(st.session_state.carrinho.items()):
            resumo_whatsapp += f"• {dados['qtd']}x {item} (R$ {formatar_preco(dados['preco'])})\n"
        resumo_whatsapp += f"\n*Endereço:* {endereco_cliente if endereco_cliente else 'Não informado'}"

        link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(resumo_whatsapp)}"

        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#25D366; color:white; padding:12px; text-align:center; border-radius:8px; font-weight:800; margin-top:10px;">
                    ✅ Finalizar no WhatsApp
                </div>
            </a>
        """, unsafe_allow_html=True)

# ---------------- CATÁLOGO MOBILE ---------------- #

df = carregar_dados()

if not df.empty:
    termo_busca = st.text_input("Buscar produto", placeholder="🔍 Digite aqui para buscar...",
                                label_visibility="collapsed")

    # Categorias em Seleção Dropdown no Mobile (Muitíssimo mais fácil de clicar)
    categorias = ["TODOS OS PRODUTOS", "BEBIDAS", "GULOSEIMAS", "DIVERSOS"]
    categoria_escolhida = st.selectbox("Filtrar por Categoria:", categorias)
    st.session_state.categoria_selecionada = categoria_escolhida

    df_filtrado = df.copy()
    if termo_busca:
        df_filtrado = df_filtrado[df_filtrado["Produto"].str.contains(termo_busca, case=False, na=False)]

    if st.session_state.categoria_selecionada != "TODOS OS PRODUTOS":
        df_filtrado = df_filtrado[df_filtrado["Categoria"] == st.session_state.categoria_selecionada]

    # Lista em coluna única para Mobile
    for indice, (_, produto) in enumerate(df_filtrado.iterrows()):
        with st.container(border=True):
            foto = produto.get("Foto")
            imagem = preparar_imagem_produto(str(foto)) if pd.notna(foto) and str(foto).strip() else Image.new("RGB",
                                                                                                               (600,
                                                                                                                480),
                                                                                                               (248,
                                                                                                                251,
                                                                                                                254))

            st.image(imagem, use_container_width=True)
            st.markdown(f'<div class="produto-titulo">{produto["Produto"]}</div>', unsafe_allow_html=True)

            preco = produto.get("Preço")
            if pd.notna(preco) and preco > 0:
                st.markdown(f'<div class="produto-preco">R$ {formatar_preco(preco)}</div>', unsafe_allow_html=True)
                st.button("🛒 Adicionar ao Pedido", key=f"mob_btn_{indice}_{produto['Produto']}", type="primary",
                          use_container_width=True, on_click=adicionar_ao_carrinho, args=(produto["Produto"], preco))