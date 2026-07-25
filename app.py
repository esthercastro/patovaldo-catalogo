import streamlit as st
import pandas as pd
import urllib.parse
import requests
from html import escape
import re

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageChops

# ---------------- CONFIGURAÇÕES ---------------- #

st.set_page_config(
    page_title="Patovaldo | Distribuidora de Bebidas e Guloseimas",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="expanded",
)

NUMERO_WHATSAPP = "+553484012444"
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1AhD1Mw0PyZ5mvZouEKkofhHovP4d4biOnXQhgLkJOWQ/"
    "export?format=csv&gid=0"
)

# Caminhos de arquivos usando busca dinâmica
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

# ---------------- ESTILO CSS SEGURO E ESTÁVEL ---------------- #

st.markdown(
    """
<style>
    :root {
        --azul: #183b5e;
        --azul-escuro: #10253c;
        --azul-claro: #eaf2f8;
        --borda: #d5e5f1;
        --dourado: #e9b83f;
        --verde-whatsapp: #25D366;
    }

    .stApp {
        background-color: #f7f9fb;
        color: var(--azul);
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem !important;
        padding-bottom: 2rem;
    }

    header[data-testid="stHeader"] {
        background-color: #101319 !important;
    }

    /* Destaque discreto do botão do carrinho no topo */
    button[data-testid="stHeaderNavStateButton"],
    button[data-testid="stSidebarCollapseButton"] {
        background-color: var(--azul) !important;
        border: 2px solid var(--dourado) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }

    .marca {
        color: var(--azul);
        font-size: 1.6rem;
        font-weight: 850;
        line-height: 1.15;
        margin: 0;
    }

    .apresentacao-catalogo {
        color: #475569;
        font-size: 0.9rem;
        line-height: 1.4;
        margin-top: 0.3rem;
        max-width: 760px;
    }

    /* Campo de Busca (Garante texto escuro e bem visível) */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #183b5e !important;
        font-weight: 600 !important;
        border: 2px solid #183b5e !important;
        border-radius: 8px !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }

    /* Cards de Produtos */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #e1e7ed !important;
        border-radius: 14px;
        box-shadow: 0 3px 10px rgba(15, 44, 71, 0.08);
        height: 100%;
        padding: 0.75rem;
    }

    .produto-titulo {
        color: var(--azul);
        font-size: 1rem;
        font-weight: 800;
        line-height: 1.2;
        margin: 0.4rem 0 0.2rem;
        text-align: center;
    }

    .produto-desc {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        line-height: 1.3;
        text-align: center;
    }

    .produto-regra-minima {
        color: #1B44BF;
        font-size: 0.8rem;
        font-weight: 700;
        line-height: 1.3;
        margin-top: 0.1rem;
        text-align: center;
    }

    .produto-preco {
        color: var(--azul);
        font-size: 1.45rem;
        font-weight: 900;
        margin: 0.4rem 0 0.5rem;
        text-align: center;
    }

    /* Estilo da Barra Lateral (Carrinho) */
    section[data-testid="stSidebar"] {
        background-color: var(--azul-escuro) !important;
    }

    .item-carrinho-titulo {
        color: #ffffff;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }

    .item-carrinho-subtotal {
        color: #e9b83f;
        font-weight: 700;
        font-size: 0.9rem;
    }

    .rodape {
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 2.5rem;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- FUNÇÕES ---------------- #

@st.cache_data
def carregar_logo(caminho):
    logo = Image.open(caminho).convert("RGBA")
    margem = 18
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
    if "drive.google.com/open?id=" in link:
        arquivo_id = link.split("id=")[1].split("&")[0]
        return f"https://drive.google.com/uc?export=view&id={arquivo_id}"
    return link


@st.cache_data(ttl=3600)
def preparar_imagem_produto(link):
    largura, altura = 700, 560
    fundo = (248, 251, 254, 255)

    try:
        resposta = requests.get(corrigir_link_imagem(link), timeout=15)
        resposta.raise_for_status()

        imagem_original = Image.open(BytesIO(resposta.content)).convert("RGBA")

        base_branca = Image.new("RGBA", imagem_original.size, (255, 255, 255, 255))
        imagem_visivel = Image.alpha_composite(base_branca, imagem_original)
        diferenca = ImageChops.difference(
            imagem_visivel.convert("RGB"),
            Image.new("RGB", imagem_original.size, "white"),
        )
        limites = diferenca.getbbox()
        imagem_recortada = imagem_original.crop(limites) if limites else imagem_original

        quadro = Image.new("RGBA", (largura, altura), fundo)
        imagem_recortada.thumbnail((600, 480), Image.Resampling.LANCZOS)

        posicao_x = (largura - imagem_recortada.width) // 2
        posicao_y = (altura - imagem_recortada.height) // 2
        quadro.alpha_composite(imagem_recortada, (posicao_x, posicao_y))

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

        df["Categoria"] = (
            df["Categoria"].fillna("DIVERSOS").astype(str).str.strip().str.upper()
        )

        if "Preço" in df.columns:
            texto_preco = (
                df["Preço"]
                .astype(str)
                .str.replace("R$", "", regex=False)
                .str.strip()
            )
            texto_preco = texto_preco.str.replace(",", ".", regex=False)
            df["Preço"] = pd.to_numeric(texto_preco, errors="coerce")

        return df.dropna(subset=["Produto"])

    except Exception as erro:
        st.error(f"Não foi possível carregar a planilha: {erro}")
        return pd.DataFrame()


def formatar_preco(preco):
    return f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_descricao_produto(descricao):
    texto = str(descricao).strip() if pd.notna(descricao) else ""
    partes = re.split(r"(?i)(pedido\s*m[ií]nimo\s*:?.*)", texto, maxsplit=1)
    descricao_html = escape(partes[0].strip())
    regra_html = escape(partes[1].strip()) if len(partes) > 1 else ""
    return descricao_html, regra_html


# ---------------- CARRINHO ---------------- #

def adicionar_ao_carrinho(nome, preco):
    if pd.isna(preco):
        preco = 0.0
    if nome in st.session_state.carrinho:
        st.session_state.carrinho[nome]["qtd"] += 1
    else:
        st.session_state.carrinho[nome] = {"preco": preco, "qtd": 1}
    st.toast(f"✅ {nome} adicionado ao carrinho!", icon="🛒")


def remover_do_carrinho(nome):
    if nome not in st.session_state.carrinho:
        return
    if st.session_state.carrinho[nome]["qtd"] > 1:
        st.session_state.carrinho[nome]["qtd"] -= 1
    else:
        del st.session_state.carrinho[nome]


def esvaziar_carrinho():
    st.session_state.carrinho = {}


def set_categoria(categoria):
    st.session_state.categoria_selecionada = categoria


# ---------------- BARRA LATERAL (CARRINHO ESTÁVEL) ---------------- #

with st.sidebar:
    total_itens = sum(item["qtd"] for item in st.session_state.carrinho.values())

    st.markdown(f"<h2 style='color:#ffffff; margin-bottom:10px;'>🛒 Seu Pedido ({total_itens})</h2>",
                unsafe_allow_html=True)

    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio. Adicione produtos do catálogo!")
    else:
        df_catalogo = carregar_dados()
        total_subitens = 0

        for item, dados in list(st.session_state.carrinho.items()):
            subtotal = dados["qtd"] * dados["preco"]
            total_subitens += subtotal

            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            st.markdown(f"<div class='item-carrinho-titulo'>{item}</div>", unsafe_allow_html=True)

            # Layout limpo para botões do carrinho
            col_botoes, col_subtotal = st.columns([2, 2])

            with col_botoes:
                btn_rem, txt_qtd, btn_add = st.columns([1, 1, 1])
                with btn_rem:
                    st.button("−", key=f"rem_{item}", on_click=remover_do_carrinho, args=(item,))
                with txt_qtd:
                    st.markdown(
                        f"<div style='text-align:center; color:#ffffff; font-weight:bold; margin-top:4px;'>{dados['qtd']}</div>",
                        unsafe_allow_html=True)
                with btn_add:
                    st.button("＋", key=f"add_{item}", on_click=adicionar_ao_carrinho, args=(item, dados["preco"]))

            with col_subtotal:
                st.markdown(
                    f"<div class='item-carrinho-subtotal' style='text-align:right; margin-top:4px;'>R$ {formatar_preco(subtotal)}</div>",
                    unsafe_allow_html=True)

        st.markdown("<hr style='margin: 1rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        st.markdown("<h4 style='color:#ffffff;'>Informações de Entrega</h4>", unsafe_allow_html=True)
        endereco_cliente = st.text_input(
            "Endereço de entrega (Obrigatório):",
            placeholder="Ex: Rua das Flores, 123"
        )

        if CAMINHO_MAPA and CAMINHO_MAPA.exists():
            st.image(str(CAMINHO_MAPA), caption="Zonas de Entrega e Taxas")

        st.divider()
        st.markdown(f"<h3 style='color:#ffffff;'>Total: R$ {formatar_preco(total_subitens)} + Taxa</h3>",
                    unsafe_allow_html=True)

        resumo_whatsapp = "Olá! Gostaria de fazer o seguinte pedido:\n\n"
        for item, dados in list(st.session_state.carrinho.items()):
            resumo_whatsapp += f"• {dados['qtd']}x {item} (R$ {formatar_preco(dados['preco'])})\n"

        resumo_whatsapp += f"\n*Subtotal dos itens:* R$ {formatar_preco(total_subitens)}"
        resumo_whatsapp += f"\n*Endereço:* {endereco_cliente if endereco_cliente else 'Não informado'}"
        resumo_whatsapp += "\n\nAguardo confirmação da disponibilidade!"

        link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(resumo_whatsapp)}"

        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#25D366; color:white; padding:12px; text-align:center; border-radius:8px; font-weight:800; font-size:1rem; margin-top:10px;">
                    ✅ Finalizar Pedido no WhatsApp
                </div>
            </a>
        """, unsafe_allow_html=True)

        st.button("🗑️ Limpar Carrinho", on_click=esvaziar_carrinho, use_container_width=True)

# ---------------- CABEÇALHO ---------------- #

col_logo, col_texto = st.columns([1.1, 5])

with col_logo:
    if CAMINHO_LOGO and CAMINHO_LOGO.exists():
        st.image(carregar_logo(str(CAMINHO_LOGO)), width=140)

with col_texto:
    st.markdown('<p class="marca">PATOVALDO DISTRIBUIDORA</p>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="apresentacao-catalogo">
            &#128230; Bebidas e Alimentos | &#128666; Entrega rápida em Patos de Minas e região
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------- BUSCA, CATEGORIAS E CATÁLOGO ---------------- #

df = carregar_dados()

if df.empty:
    st.warning("Nenhum produto encontrado. Verifique sua planilha.")
else:
    termo_busca = st.text_input(
        "Buscar produto",
        placeholder="🔍 Ex: Cachaça 51, Chiclete...",
        label_visibility="collapsed",
    )

    categorias_botoes = {
        "TODOS OS PRODUTOS": "🛒 Todos",
        "BEBIDAS": "🥤 Bebidas",
        "GULOSEIMAS": "🍬 Guloseimas",
        "DIVERSOS": "📦 Diversos",
    }

    colunas_botoes = st.columns(len(categorias_botoes))
    for indice, (chave, rotulo) in enumerate(categorias_botoes.items()):
        with colunas_botoes[indice]:
            ativo = st.session_state.categoria_selecionada == chave
            st.button(
                rotulo,
                key=f"categoria_{chave}",
                type="primary" if ativo else "secondary",
                use_container_width=True,
                on_click=set_categoria,
                args=(chave,),
            )

    df_filtrado = df.copy()
    if termo_busca:
        df_filtrado = df_filtrado[
            df_filtrado["Produto"].str.contains(termo_busca, case=False, na=False)
            | df_filtrado["Descrição"].astype(str).str.contains(termo_busca, case=False, na=False)
            ]

    if st.session_state.categoria_selecionada != "TODOS OS PRODUTOS":
        df_filtrado = df_filtrado[
            df_filtrado["Categoria"] == st.session_state.categoria_selecionada
            ]

    st.markdown("<br>", unsafe_allow_html=True)

    if df_filtrado.empty:
        st.info("Nenhum produto encontrado com estes filtros.")
    else:
        colunas_produtos = st.columns(4)

        for indice, (_, produto) in enumerate(df_filtrado.iterrows()):
            with colunas_produtos[indice % 4]:
                with st.container(border=True):
                    foto = produto.get("Foto")
                    if pd.notna(foto) and str(foto).strip():
                        imagem = preparar_imagem_produto(str(foto))
                    else:
                        imagem = Image.new("RGB", (700, 560), (248, 251, 254))

                    st.image(imagem, use_container_width=True)
                    st.markdown(
                        f'<div class="produto-titulo">{produto["Produto"]}</div>',
                        unsafe_allow_html=True,
                    )

                    descricao, regra_minima = formatar_descricao_produto(
                        produto.get("Descrição", "")
                    )
                    if descricao:
                        st.markdown(
                            f'<div class="produto-desc">{descricao}</div>',
                            unsafe_allow_html=True,
                        )
                    if regra_minima:
                        st.markdown(
                            f'<div class="produto-regra-minima">{regra_minima}</div>',
                            unsafe_allow_html=True,
                        )

                    preco = produto.get("Preço")
                    if pd.notna(preco) and preco > 0:
                        st.markdown(
                            f'<div class="produto-preco">R$ {formatar_preco(preco)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            "Adicionar",
                            key=f"adicionar_{indice}_{produto['Produto']}",
                            type="primary",
                            use_container_width=True,
                            on_click=adicionar_ao_carrinho,
                            args=(produto["Produto"], preco),
                        )
                    else:
                        st.markdown(
                            '<div class="produto-preco" style="font-size:1.1rem;">Sob consulta</div>',
                            unsafe_allow_html=True,
                        )
                        st.button(
                            "Consultar",
                            key=f"consultar_{indice}_{produto['Produto']}",
                            type="secondary",
                            use_container_width=True,
                        )

st.markdown('<p class="rodape">© 2026 Patovaldo Distribuidora</p>', unsafe_allow_html=True)