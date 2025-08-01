# app.py
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from questions_map import get_question_map

# ---------------- Configuração ----------------
st.set_page_config(
    page_title="POC Expressa - E-commerce (IA opcional)",
    layout="wide"
)

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background-color: #0e1117;
        color: #FFFFFF;
    }
    h1, h2, h3 { color: #00CED1 !important; }
    .stApp, .stMarkdown, .stDataFrame, .stExpander,
    .stMetric, .stSelectbox, .stTextInput {
        background-color: #1a1c22 !important;
        border-radius: 10px !important;
        color: #FFFFFF !important;
    }
    .stButton > button {
        background-color: #00CED1;
        color: black;
        font-weight: bold;
        border-radius: 6px;
    }
    .stSlider > div > div { background-color: #1a1c22; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb {
        background-color: #00CED1;
        border-radius: 6px;
    }
    .stChatInputContainer, .stChatMessage {
        background-color: #1a1c22 !important;
        color: #ffffff !important;
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("POC Expressa de E-commerce — Modo IA Opcional")

# ---------------- IA opcional ----------------
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.sidebar.header("⚙️ Configurações")
USE_IA = st.sidebar.toggle("Usar IA para explicar respostas", value=False)
AGENTE = st.sidebar.selectbox(
    "Tipo de agente (perfil de explicação)",
    ["Executivo de Vendas", "Analista de BI", "Gestor Geral"],
    disabled=not USE_IA,
)
OPENROUTER_API_KEY = (
    st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    if USE_IA else ""
)
MODEL_NAME = st.sidebar.text_input(
    "Modelo (OpenRouter)",
    value="mistralai/mistral-7b-instruct",
    disabled=not USE_IA
)
MAX_NUMBERS = st.sidebar.slider(
    "Quantos números no resumo enviado à IA",
    min_value=20, max_value=200, value=60, disabled=not USE_IA
)

with st.sidebar.expander("❓ O que significam esses parâmetros?"):
    st.markdown("""
    **Usar IA para explicar respostas:** gera explicação em linguagem natural em português.  
    **Modelo:** modelo de IA consultado via OpenRouter.  
    **Quantos números:** limite de valores numéricos enviados à IA.  
    """)

# ---------------- Helpers de formatação ----------------
def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0

def fmt_int(x: int) -> str:
    return f"{x:,}".replace(",", ".")

def fmt_money(x: float) -> str:
    s = f"{x:,.2f}"
    return s.replace(".", "v").replace(",", ".").replace("v", ",")

# ---------------- Carregamento de dados ----------------
@st.cache_data
def carregar_dados():
    try:
        clientes = pd.read_csv("data/clients.csv")
        pedidos  = pd.read_csv("data/orders.csv")
        itens    = pd.read_csv("data/items.csv")
        produtos = pd.read_csv("data/products.csv")
        return clientes, pedidos, itens, produtos, None
    except Exception as e:
        return None, None, None, None, str(e)

# ---------------- Cliente IA ----------------
def build_client():
    if not USE_IA:
        return None, None
    if not OPENROUTER_API_KEY:
        return None, "API key não encontrada."
    if OpenAI is None:
        return None, "Pacote openai não instalado."
    try:
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        ), None
    except Exception as e:
        return None, f"Erro ao criar cliente IA: {e}"

# ---------------- Métricas determinísticas ----------------
def answer_ticket_medio(pedidos: pd.DataFrame) -> dict:
    df = pedidos[pedidos["SituacaoPedido"].str.lower() == "faturado"]
    media = df["TotalPedido"].apply(safe_float).mean()
    return {"titulo": "Ticket médio", "valor": round(media, 2)}

def answer_desconto_medio(pedidos: pd.DataFrame) -> dict:
    df = pedidos[pedidos["SituacaoPedido"].str.lower() == "faturado"]
    media = df["ValorDesconto"].apply(safe_float).mean()
    return {"titulo": "Desconto médio", "valor": round(media, 2)}

def top_produtos(itens: pd.DataFrame, produtos: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    top = (
        itens.groupby("CodigoProdutoVendido")["QuantidadeVendidaItem"]
             .sum()
             .nlargest(n)
             .reset_index()
    )
    top = top.merge(
        produtos.drop_duplicates(subset="CodigoProduto"),
        left_on="CodigoProdutoVendido", right_on="CodigoProduto",
        how="left"
    )
    return top[["Produto", "QuantidadeVendidaItem"]]

def formas_pagamento(pedidos: pd.DataFrame) -> pd.DataFrame:
    fp = pedidos["FormaPagamento"].value_counts().reset_index()
    fp.columns = ["Forma de Pagamento", "Total"]
    return fp

def frete_gratis_count(pedidos: pd.DataFrame) -> dict:
    cnt = pedidos[
        pedidos["FreteGratis"].astype(str).str.lower().isin(["sim","s","true","1"])
    ].shape[0]
    return {"titulo": "Pedidos com frete grátis", "valor": cnt}

def status_pedidos(pedidos: pd.DataFrame) -> pd.DataFrame:
    stts = pedidos["SituacaoPedido"].value_counts().reset_index()
    stts.columns = ["Situação", "Total"]
    return stts

def tipo_cliente(pedidos: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    merged = pedidos.merge(
        clientes, left_on="CodigoClientePedido",
        right_on="CodigoCliente", how="left"
    )
    tc = merged["TipoCliente"].value_counts().reset_index()
    tc.columns = ["Tipo de Cliente", "Total de Pedidos"]
    return tc

def grafico_ticket_medio(pedidos: pd.DataFrame):
    df = pedidos[pedidos["SituacaoPedido"].str.lower() == "faturado"].copy()
    df["DataPedido"] = pd.to_datetime(df["DataPedido"], errors="coerce")
    df["TotalPedido"] = df["TotalPedido"].apply(safe_float)
    df = df.dropna(subset=["DataPedido", "TotalPedido"])
    df["Mês"] = df["DataPedido"].dt.to_period("M").astype(str)
    grp = df.groupby("Mês")["TotalPedido"].mean().reset_index()
    return px.line(grp, x="Mês", y="TotalPedido", title="Ticket médio mensal")

# ---------------- Helpers IA ----------------
def default_system_prompt(agente: str) -> str:
    perfil = {
        "executivo": "Você é um executivo comercial. Seja direto e focado em impacto.",
        "analista de bi": "Você é um analista de BI. Explique com detalhes e fórmulas.",
        "gestor geral": "Você é um gestor geral. Foque em impacto e clareza."
    }.get(agente.lower(), "")
    instrução = "Responda sempre em português, a menos que o usuário peça outro idioma."
    return f"{perfil} {instrução}"

def summarize_numbers_for_llm(d: dict, limit: int = 60) -> str:
    flat = []
    def walk(x):
        if isinstance(x, dict):
            for v in x.values(): walk(v)
        elif isinstance(x, (list, tuple, set)):
            for v in x: walk(v)
        else:
            try: flat.append(float(x))
            except: pass
    walk(d)
    return ", ".join(f"{v:.4f}" for v in flat[:limit])

def ask_model_explain(
    client, model: str, question: str, result: dict,
    max_numbers: int = 60, temperature: float = 0.1, agente: str = "Gestor Geral"
):
    if not client:
        return None, "Cliente IA não disponível."
    nums = summarize_numbers_for_llm(result, limit=max_numbers)
    content = (
        f"Pergunta do usuário: {question}\n"
        f"Números disponíveis: {nums}\n"
        f"Resultado calculado: {result}"
    )
    try:
        comp = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system", "content": default_system_prompt(agente)},
                {"role":"user",   "content": content}
            ],
            temperature=temperature
        )
        return comp.choices[0].message.content, None
    except Exception as e:
        return None, f"Erro IA: {e}"

def ask_model_fallback(
    client, model: str, question: str,
    clientes, pedidos, itens, produtos, max_numbers: int = 60
):
    snapshot = {
        "total_pedidos": int(pedidos.shape[0]),
        "ticket_medio": round(answer_ticket_medio(pedidos)["valor"], 2),
        "desconto_medio": round(answer_desconto_medio(pedidos)["valor"], 2),
    }
    return ask_model_explain(client, model, question, snapshot, max_numbers=max_numbers)

# ---------------- Roteamento de perguntas ----------------
def route_question(pergunta: str, clientes, pedidos, itens, produtos):
    q = pergunta.lower()

    # mapeamento explícito
    if "quantos pedidos têm frete grátis" in q:
        return "frete_gratis", frete_gratis_count(pedidos)

    mapa = get_question_map()
    for intent, meta in mapa.items():
        for exemplo in meta["exemplos"]:
            if exemplo in q:
                fn = meta["funcao"]
                return intent, {
                    "answer_ticket_medio": answer_ticket_medio(pedidos),
                    "answer_desconto_medio": answer_desconto_medio(pedidos),
                    "top_produtos": top_produtos(itens, produtos),
                    "formas_pagamento": formas_pagamento(pedidos),
                    "status_pedidos": status_pedidos(pedidos),
                    "tipo_cliente": tipo_cliente(pedidos, clientes),
                }[fn]
    return "nao_mapeado", None

# ---------------- Execução principal ----------------
clientes, pedidos, itens, produtos, erro = carregar_dados()
if erro:
    st.error(f"Erro ao carregar dados: {erro}")
    st.stop()
else:
    st.success("✅ Dados carregados com sucesso!")

# KPIs iniciais
col1, col2 = st.columns(2)
col1.metric("📦 Pedidos", fmt_int(pedidos.shape[0]))
tm = answer_ticket_medio(pedidos)["valor"]
col2.metric("💰 Ticket Médio", f"R$ {fmt_money(tm)}")

st.header("💬 Pergunte aos dados")

client, client_err = build_client()
if client_err:
    st.sidebar.error(client_err)

if "messages" not in st.session_state:
    st.session_state.messages = []

# exibir histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Ex: Quantos pedidos têm frete grátis?")
if pergunta:
    st.session_state.messages.append({"role":"user","content":pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    intent, resultado = route_question(pergunta, clientes, pedidos, itens, produtos)

    with st.chat_message("assistant"):
        # não mapeado → fallback IA
        if resultado is None:
            if USE_IA:
                with st.spinner("Consultando IA para resposta geral..."):
                    explic, err = ask_model_fallback(
                        client, MODEL_NAME, pergunta,
                        clientes, pedidos, itens, produtos,
                        max_numbers=MAX_NUMBERS
                    )
                if err:
                    st.error(err)
                else:
                    st.markdown(explic)
            else:
                st.warning("❗ Pergunta não mapeada. Ative IA para resposta geral.")
        else:
            # DataFrame
            if isinstance(resultado, pd.DataFrame):
                st.dataframe(resultado)
                fig = px.bar(
                    resultado,
                    x=resultado.columns[0],
                    y=resultado.columns[1],
                    title=resultado.columns[0]
                )
                st.plotly_chart(fig, use_container_width=True)

            # Métrica única
            else:
                title = resultado["titulo"]
                value = resultado["valor"]
                disp = fmt_int(int(value)) if isinstance(value, int) else fmt_money(value)
                st.subheader(title)
                st.metric("Valor", disp)
                if intent == "answer_ticket_medio":
                    st.plotly_chart(grafico_ticket_medio(pedidos), use_container_width=True)

            # explicação IA adicional
            if USE_IA:
                with st.spinner("Explicando com IA..."):
                    exp, err = ask_model_explain(
                        client, MODEL_NAME, pergunta, resultado,
                        max_numbers=MAX_NUMBERS, agente=AGENTE
                    )
                if err:
                    st.error(err)
                else:
                    st.markdown(exp)

    # registra no histórico
    st.session_state.messages.append({"role":"assistant","content":"(resposta acima)"})
