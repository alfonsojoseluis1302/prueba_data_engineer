"""Interfaz Streamlit para el agente conversacional RetailTech."""

import streamlit as st
from app.config import MELI_YELLOW, MELI_DARK_BLUE, MELI_BLUE, MELI_TEXT, SUGGESTED_QUESTIONS
from app.api_client import check_health, create_session, send_message


# ── Page config ──
st.set_page_config(
    page_title="RetailTech Agent",
    page_icon="🛒",
    layout="wide",
)

# ── Custom CSS (MeLi colors) ──
st.markdown(f"""
<style>
    .stApp {{
        background-color: #EEEEEE;
    }}
    .main-header {{
        background-color: {MELI_YELLOW};
        padding: 1rem 2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    .main-header h1 {{
        color: {MELI_DARK_BLUE};
        margin: 0;
        font-size: 1.8rem;
    }}
    .main-header p {{
        color: {MELI_TEXT};
        margin: 0;
        font-size: 0.9rem;
    }}
    .status-online {{
        color: #00a650;
        font-weight: bold;
    }}
    .status-offline {{
        color: #ff4444;
        font-weight: bold;
    }}
    .pii-badge {{
        background-color: #ff6b6b;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }}
    .stChatMessage {{
        background-color: white;
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="main-header">
    <h1>🛒 RetailTech S.A.S — Agente Analítico</h1>
    <p>Asistente de datos para e-commerce en Latinoamérica</p>
</div>
""", unsafe_allow_html=True)

# ── Session state init ──
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ──
with st.sidebar:
    st.markdown(f"### ⚙️ Estado del sistema")

    health = check_health()
    api_status = health.get("status", "offline")

    if api_status in ("healthy", "degraded"):
        st.markdown(f'<span class="status-online">● API Online</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-offline">● API Offline</span>', unsafe_allow_html=True)
        st.warning("La API no está disponible. Ejecute: `make agent-api`")

    ollama_ok = health.get("ollama_connected", False)
    duckdb_ok = health.get("duckdb_connected", False)
    st.markdown(f"- Ollama: {'✅' if ollama_ok else '❌'} ({health.get('model', 'N/A')})")
    st.markdown(f"- DuckDB: {'✅' if duckdb_ok else '❌'}")

    st.markdown("---")
    st.markdown("### 🔧 Herramientas del agente")
    st.markdown("- `ejecutar_sql` — Consultas SQL")
    st.markdown("- `obtener_esquema` — Esquemas de tablas")
    st.markdown("- `resumir_reporte_calidad` — Reportes")

    st.markdown("---")
    st.markdown("### 💡 Preguntas sugeridas")
    for q in SUGGESTED_QUESTIONS:
        if st.button(q, key=f"suggested_{q}", use_container_width=True):
            st.session_state.pending_question = q

    st.markdown("---")
    if st.button("🔄 Nueva conversación", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

# ── Auto-create session ──
if st.session_state.session_id is None:
    session_id = create_session()
    if session_id:
        st.session_state.session_id = session_id
    else:
        st.error("No se pudo crear sesión. Verifique que la API esté corriendo.")
        st.stop()

# ── Chat history ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("pii_filtered"):
            st.markdown('<span class="pii-badge">PII filtrada</span>', unsafe_allow_html=True)
        if msg.get("reasoning_steps"):
            with st.expander("🧠 Razonamiento del agente"):
                for step in msg["reasoning_steps"]:
                    step_type = step.get("type", "")
                    if step_type == "tool_call":
                        st.markdown(f"**🔧 Tool:** `{step.get('tool')}`")
                        st.code(str(step.get("args", {})), language="json")
                    elif step_type == "tool_result":
                        st.markdown("**📊 Resultado:**")
                        st.code(step.get("result", ""), language="text")
                    elif step_type == "llm_response":
                        st.markdown(f"**💭 Pensamiento:** {step.get('content', '')[:300]}...")

# ── Handle suggested question ──
pending = st.session_state.pop("pending_question", None)

# ── Chat input ──
user_input = st.chat_input("Escribe tu pregunta sobre los datos...")

# Use pending question if no direct input
question = user_input or pending

if question:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Send to API
    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            result = send_message(st.session_state.session_id, question)

        answer = result.get("answer", "Sin respuesta")
        st.markdown(answer)

        pii_filtered = result.get("pii_filtered", False)
        if pii_filtered:
            st.markdown('<span class="pii-badge">PII filtrada</span>', unsafe_allow_html=True)

        reasoning = result.get("reasoning_steps", [])
        if reasoning:
            with st.expander("🧠 Razonamiento del agente"):
                for step in reasoning:
                    step_type = step.get("type", "")
                    if step_type == "tool_call":
                        st.markdown(f"**🔧 Tool:** `{step.get('tool')}`")
                        st.code(str(step.get("args", {})), language="json")
                    elif step_type == "tool_result":
                        st.markdown("**📊 Resultado:**")
                        st.code(step.get("result", ""), language="text")
                    elif step_type == "llm_response":
                        st.markdown(f"**💭 Pensamiento:** {step.get('content', '')[:300]}...")

        tools_used = result.get("tools_used", [])
        if tools_used:
            st.caption(f"Herramientas usadas: {', '.join(tools_used)}")

    # Save to state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "reasoning_steps": reasoning,
        "pii_filtered": pii_filtered,
    })
