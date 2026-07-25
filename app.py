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

# Define a pasta raiz do projeto usando caminho absoluto
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

if "carrinho" not in st.session_state:
    st.session_state.carrinho = {}

if "categoria_selecionada" not in st.session_state:
    st.session_state.categoria_selecionada = "TODOS OS PRODUTOS"

# ---------------- ESTILO CSS CORRIGIDO ---------------- #

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
        max-width: 1500px;
        padding-top: 2rem !important;
        padding-bottom: 3rem;
    }

    header[data-testid="stHeader"] {
        background-color: #101319;
    }

    .marca {
        color: var(--azul);
        font-size: 1.7rem;
        font-weight: 850;
        line-height: 1.15;
        margin: 0;
    }

    .subtitulo {
        color: var(--dourado);
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: 0.08rem;
        margin: 0.25rem 0 0;
        text-transform: uppercase;
    }

    .apresentacao-catalogo {
        color: #475569;
        font-size: 0.96rem;
        line-height: 1.5;
        margin-top: 0.45rem;
        max-width: 760px;
    }

    /* CORREÇÃO 1: Campo de Busca (Garante texto escuro e visível) */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #183b5e !important; /* Cor do texto digitado */
        font-weight: 600 !important;
        border: 2px solid #183b5e !important;
        border-radius: 8px !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important; /* Cor do texto de dica (placeholder) */
        opacity: 1 !important;
    }

    /* CORREÇÃO 2: Estilo do aviso do carrinho para telemóveis */
    .alerta-carrinho-mobile {
        background-color: #183b5e;
        color: #ffffff;
        padding: 10px 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 15px;
        border: 2px solid #e9b83f;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #e1e7ed !important;
        border-radius: 16px;
        box-shadow: 0 3px 10px rgba(15, 44, 71, 0.10);
        height: 100%;
        min-height: 0;
        overflow: hidden;
        padding: 0.75rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #9dbbd4 !important;
        box-shadow: 0 9px 22px rgba(24, 59, 94, 0.18);
        transform: translateY(-2px);
        transition: 0.2s ease;
    }

    .produto-titulo {
        color: var(--azul);
        font-size: 1.02rem;
        font-weight: 800;
        line-height: 1.25;
        margin: 0.55rem 0 0.2rem;
        min-height: 0;
        text-align: center;
    }

    .produto-desc {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        line-height: 1.35;
        min-height: 0;
        text-align: center;
    }

    .produto-regra-minima {
        color: #1B44BF;
        font-size: 0.8rem;
        font-weight: 700;
        line-height: 1.35;
        margin-top: 0.1rem;
        text-align: center;
    }

    .produto-preco {
        color: var(--azul);
        font-size: 1.55rem;
        font-weight: 900;
        margin: 0.45rem 0 0.55rem;
        text-align: center;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stImage"] img {
        border-radius: 8px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="primary"] {
        border-radius: 999px;
        min-height: 2.8rem;
    }

    button[kind="primary"] {
        background-color: var(--azul) !important;
        border: 2px solid var(--azul) !important;
        border-radius: 9px;
        color: #ffffff !important;
        font-weight: 750;
    }

    button[kind="primary"]:hover {
        background-color: var(--dourado) !important;
        border-color: var(--dourado) !important;
        color: var(--azul) !important;
    }

    [class*="st-key-categoria_"] button {
        background-color: #ffffff !important;
        border: 2px solid var(--azul) !important;
        color: var(--azul) !important;
    }

    [class*="st-key-categoria_"] button[kind="primary"],
    [class*="st-key-categoria_"] button[kind="primary"]:hover {
        background-color: #183B5E !important;
        border-color: #183B5E !important;
        color: #ffffff !important;
    }

    [class*="st-key-categoria_"] button[kind="secondary"]:hover {
        background-color: #f2f6fa !important;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--azul-escuro) !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        border-radius: 6px;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: #ffffff !important;
    }

    section[data-testid="stSidebar"] div[data-testid="column"] .stButton {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 2px;
    }

    section[data-testid="stSidebar"] div[data-testid="column"] .stButton button {
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 6px !important;
        font-size: 1.2rem !important;
        line-height: 1 !important;
        position: relative !important;
    }

    section[data-testid="stSidebar"] div[data-testid="column"] .stButton button > * {
        position: absolute !important;
        inset: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    section[data-testid="stSidebar"] div[data-testid="column"] .stButton button p,
    section[data-testid="stSidebar"] div[data-testid="column"] .stButton button span {
        margin: 0 !important;
        line-height: 1 !important;
        transform: none !important;
    }

    .qtd-valor {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 32px;
        font-weight: bold;
        font-size: 1.15rem;
        color: #ffffff;
        margin-top: 2px;
    }

    .subtotal-valor {
        text-align: right;
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 6px;
    }

    .rodape {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 3rem;
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
    st.toast(f"✅ {nome} adicionado! Clique na seta '>>' no topo superior para ver seu pedido.", icon="🛒")


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


# ---------------- BARRA LATERAL (CARRINHO) ---------------- #

with st.sidebar:
    total_itens = sum(item["qtd"] for item in st.session_state.carrinho.values())
    st.title(f"🛒 Seu Pedido ({total_itens} itens)")

    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio. Adicione produtos do catálogo!")
    else:
        df_catalogo = carregar_dados()

        st.markdown(
            "<p style='color:#e9b83f; font-weight:700; margin-bottom:5px; font-size:1.1rem;'>Resumo do Pedido</p>",
            unsafe_allow_html=True)

        total_subitens = 0

        for item, dados in list(st.session_state.carrinho.items()):
            subtotal = dados["qtd"] * dados["preco"]
            total_subitens += subtotal

            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

            linha_produto = df_catalogo[df_catalogo["Produto"] == item]
            link_foto = linha_produto["Foto"].iloc[0] if not linha_produto.empty else None

            col_img, col_info = st.columns([1.2, 3.8], gap="small")

            with col_img:
                if pd.notna(link_foto) and str(link_foto).strip():
                    st.image(preparar_imagem_produto(str(link_foto)), use_container_width=True)
                else:
                    imagem_vazia = Image.new("RGB", (700, 560), (248, 251, 254))
                    st.image(imagem_vazia, use_container_width=True)

            with col_info:
                c_nome, c_tag_sub = st.columns([2.5, 1.5])
                with c_nome:
                    st.markdown(
                        f"<div style='font-size:0.95rem; font-weight:700; color:#ffffff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{item}</div>",
                        unsafe_allow_html=True)
                with c_tag_sub:
                    st.markdown("<div style='font-size:0.8rem; color:#9dbbd4; text-align:right;'>Subtotal</div>",
                                unsafe_allow_html=True)

                c_menos, c_qtd, c_mais, c_sub = st.columns([0.8, 0.8, 0.8, 2.5])
                with c_menos:
                    st.button("−", key=f"rem_{item}", on_click=remover_do_carrinho, args=(item,))
                with c_qtd:
                    st.markdown(f"<div class='qtd-valor'>{dados['qtd']}</div>", unsafe_allow_html=True)
                with c_mais:
                    st.button("＋", key=f"add_{item}", on_click=adicionar_ao_carrinho, args=(item, dados["preco"]))
                with c_sub:
                    st.markdown(f"<div class='subtotal-valor'>R$ {formatar_preco(subtotal)}</div>",
                                unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0.5rem 0 1.5rem 0; border-color: rgba(255,255,255,0.08);'>",
                    unsafe_allow_html=True)

        st.markdown("### Informações de Entrega")
        st.info("Consulte o mapa abaixo para verificar a taxa de entrega da sua região.")

        endereco_cliente = st.text_input(
            "Endereço de entrega (Obrigatório):",
            placeholder="Ex: Rua das Flores, 123 - Centro"
        )

        if CAMINHO_MAPA and CAMINHO_MAPA.exists():
            st.image(str(CAMINHO_MAPA), caption="Zonas de Entrega e Taxas")
        else:
            st.markdown(
                """
                <div style="text-align: center; margin-top: 10px;">
                    <img src="https://dummyimage.com/600x400/183b5e/ffffff&text=Mapa+Satelite+-+Faixas+de+Preço" style="width: 100%; border-radius: 8px;">
                    <p style="font-size: 0.8rem; color: #9dbbd4; margin-top: 5px;">Consulte as faixas de preço no mapa acima.</p>
                </div>
                """, unsafe_allow_html=True
            )

        st.divider()
        st.markdown(f"### Total: R$ {formatar_preco(total_subitens)} + Taxa de Entrega")

        st.caption("⚠️ Pedido mínimo varia conforme a região.")
        st.caption(
            "Por enquanto, aceitamos pagamentos via Pix ou no ato da entrega. Em breve, também disponibilizaremos pagamentos com cartão de crédito e débito para oferecer ainda mais comodidade.")

        resumo_whatsapp = "Olá! Gostaria de fazer o seguinte pedido:\n\n"

        for item, dados in list(st.session_state.carrinho.items()):
            resumo_whatsapp += f"• {dados['qtd']}x {item} (R$ {formatar_preco(dados['preco'])})\n"

        resumo_whatsapp += f"\n*Subtotal dos itens:* R$ {formatar_preco(total_subitens)}"
        resumo_whatsapp += f"\n*Endereço:* {endereco_cliente if endereco_cliente else 'Não informado'}"
        resumo_whatsapp += "\n*Taxa de entrega:* A combinar (conforme mapa de zonas)"
        resumo_whatsapp += f"\n\n*Total aproximado:* R$ {formatar_preco(total_subitens)} + Taxa de Entrega"
        resumo_whatsapp += "\n\nAguardo confirmação da disponibilidade!"

        link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(resumo_whatsapp)}"

        st.markdown(f"""
            <a href="{link_whatsapp}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#25D366; color:white; padding:12px; text-align:center; border-radius:9px; font-weight:800; font-size:1.05rem; margin-bottom:15px; margin-top:10px;">
                    ✅ Finalizar meu pedido no WhatsApp
                </div>
            </a>
        """, unsafe_allow_html=True)

        st.button("🗑️ Limpar Carrinho", on_click=esvaziar_carrinho, use_container_width=True)

# ---------------- CABEÇALHO ---------------- #

# Indicador em destaque no topo para telemóveis informando sobre o carrinho
total_itens_atual = sum(item["qtd"] for item in st.session_state.carrinho.values())
if total_itens_atual > 0:
    st.markdown(
        f"""
        <div class="alerta-carrinho-mobile">
            🛒 <b>Seu Pedido tem {total_itens_atual} item(ns)!</b><br>
            <span style="font-size:0.85rem; font-weight:normal;">Clique na seta <b>'>>'</b> no canto superior esquerdo para ver o carrinho e finalizar.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

col_logo, col_texto = st.columns([1.1, 5])

with col_logo:
    if CAMINHO_LOGO and CAMINHO_LOGO.exists():
        st.image(carregar_logo(str(CAMINHO_LOGO)), width=175)
    else:
        st.warning("Logo não encontrada na pasta assets/.")

with col_texto:
    st.markdown(
        '<p class="marca">PATOVALDO DISTRIBUIDORA ATACADO E VAREJO</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="apresentacao-catalogo">
            &#128230; Bebidas e Alimentos para estabelecimentos e festas<br>
            &#128666; Entrega rápida em Patos de Minas e região<br>
            &#128071; Confira nosso catálogo e faça seu pedido<br>
            Para realizar seu pedido, basta escolher os produtos e a quantidade desejada.
            Depois de fazer a seleção, seu pedido será finalizado via WhatsApp.
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