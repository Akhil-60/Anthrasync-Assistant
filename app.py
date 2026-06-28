
"""Anthrasync Knowledge Assistant - AI chatbot UI with live streaming. Run: streamlit run app.py"""

import base64
import os
from datetime import datetime

import streamlit as st

from src.pipeline import RAGPipeline

ACCENT = "#2D8CFF"
LOGO_PATH = "anthrasync_logo.png"
WORDMARK_PATH = "anthrasync_wordmark.png"
ASSISTANT_AVATAR = LOGO_PATH if os.path.exists(LOGO_PATH) else None
USER_AVATAR = "anthrasync_logo1.png"
WELCOME = (
    "### \U0001F44B Welcome to Anthrasync AI\n\n"
    
    "Ask your question below to get started."
)

EXAMPLES = [
    ("\U0001F4C4 HR Policy", "What is the employee leave policy?"),
    ("\U0001F4B0 Refund Policy", "What is the refund policy?"),
    ("\U0001F3E2 About Anthrasync", "What does Anthrasync do?"),
    ("\U0001F4BB IT Support", "Who do I contact for server failure?"),
]


def now_time():
    return datetime.now().strftime("%I:%M %p")


st.set_page_config(page_title="Anthrasync Assistant", layout="centered")

st.markdown(
    "<style>"
    ".stApp{background-color:#07070A;"
    "background-image:"
    "radial-gradient(circle at 18% 28%, rgba(45,140,255,0.20), transparent 42%),"
    "radial-gradient(circle at 82% 22%, rgba(124,77,255,0.16), transparent 42%),"
    "radial-gradient(circle at 62% 82%, rgba(45,140,255,0.14), transparent 42%),"
    "radial-gradient(circle at 30% 75%, rgba(0,200,255,0.10), transparent 42%);"
    "background-size:200% 200%,200% 200%,200% 200%,200% 200%;"
    "animation:aiflow 22s ease infinite;}"
    "@keyframes aiflow{"
    "0%{background-position:0% 50%,100% 50%,50% 0%,50% 100%;}"
    "50%{background-position:100% 50%,0% 50%,50% 100%,50% 0%;}"
    "100%{background-position:0% 50%,100% 50%,50% 0%,50% 100%;}}"
    ".block-container{max-width:820px;}"
    ".wordmark{width:230px;mix-blend-mode:screen;display:block;margin:6px 0 0 -6px;}"
    ".brand-sub{color:#9A9AA2;font-size:.9rem;margin:2px 0 20px 2px;}"
    ".brand-name{font-size:1.45rem;font-weight:700;color:#fff;}"
    ".stamp{color:#5A5A62;font-size:.72rem;margin:2px 0 0 2px;}"
    ".dot{height:8px;width:8px;background:" + ACCENT + ";border-radius:50%;display:inline-block;"
    "margin-right:6px;box-shadow:0 0 8px " + ACCENT + ";animation:pulse 1.6s ease-in-out infinite;}"
    "@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.35;}}"
    ".foot{text-align:center;color:#5A5A62;font-size:.8rem;margin-top:26px;}"
    ".stButton>button{width:100%;border-radius:10px;background:#161B22;"
    "border:1px solid rgba(255,255,255,.10);color:#fff;}"
    ".stButton>button:hover{border:1px solid " + ACCENT + ";background:#1F2937;}"
    "section[data-testid='stSidebar']{background:#0D1117;}"
    "</style>",
    unsafe_allow_html=True,
)


def _img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


if os.path.exists(WORDMARK_PATH):
    st.markdown(
        f"<img class='wordmark' src='data:image/png;base64,{_img_b64(WORDMARK_PATH)}'/>"
        "<div class='brand-sub'>AI Knowledge Assistant &mdash; grounded in the company "
        "knowledge base. <span style='color:" + ACCENT + "'><span class='dot'></span>online</span></div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div style='margin-bottom:18px'>"
        "<span class='brand-name'>Anthr<span style='color:" + ACCENT + "'>a</span>sync</span>"
        "<div class='brand-sub'>AI Knowledge Assistant &mdash; grounded in the company knowledge base.</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def stamp(t):
    if t:
        st.markdown(f"<div class='stamp'>{t}</div>", unsafe_allow_html=True)


@st.cache_resource
def get_pipeline():
    return RAGPipeline()


try:
    pipeline = get_pipeline()
except Exception as exc:
    st.error(f"Startup failed: {exc}")
    st.info("Run python -m src.ingest first and set GEMINI_API_KEY in .env.")
    st.stop()

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=64)
    st.markdown("## Anthrasync AI")
    st.success("\U0001F7E2 Online")
    st.caption("Enterprise Knowledge Assistant")
    st.divider()
    if st.button("\u2795 New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button("\U0001F5D1 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.subheader("\U0001F4DA Knowledge Base")
    st.markdown("- HR Policies\n- Product Documentation\n- Technical Guides\n"
                "- Customer FAQs\n- Compliance\n- Company Overview")
    st.divider()
    st.subheader("\u2699 System")
    st.markdown("**LLM:** Gemini\n\n**Vector DB:** ChromaDB\n\n"
                "**Retriever:** Semantic search\n\n**Status:** Ready")

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        st.markdown(WELCOME)

for m in st.session_state.messages:

    avatar = ASSISTANT_AVATAR if m["role"] == "assistant" else USER_AVATAR
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])
        stamp(m.get("time"))

queued = None
if not st.session_state.messages:
    st.caption("Try one of these:")
    cols = st.columns(2)
    for i, (label, question) in enumerate(EXAMPLES):
        if cols[i % 2].button(label, key=f"ex{i}"):
            queued = question

typed = st.chat_input("Ask anything about the company, in any language...")
q = typed or queued
if q:
    t_user = now_time()
    st.session_state.messages.append({"role": "user", "content": q, "time": t_user})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(q)
        stamp(t_user)
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        answer = st.write_stream(pipeline.stream_ask(q))
        t_bot = now_time()
        stamp(t_bot)
    st.session_state.messages.append({"role": "assistant", "content": answer, "time": t_bot})
    if queued:
        st.rerun()

st.markdown(
    "<div class='foot'>Powered by <span style='color:" + ACCENT + ";font-weight:600'>Anthrasync AI</span> "
    "&middot; RAG + Gemini</div>",
    unsafe_allow_html=True,
)
