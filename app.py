# app.py (Updated UI + Integrated with FastAPI)
import os
import json
import requests
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any
from helper import current_year, save_to_audio, rating_to_stars

# === UI Configuration ===
st.set_page_config(page_title="InsightFOX 🦊", page_icon="🔍", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f4f4f4; color: #111; font-family: 'Segoe UI', sans-serif;}
        .stButton>button {
            background-color: #0066cc;
            color: white;
            font-weight: 600;
            border-radius: 0.5rem;
            padding: 0.5em 1em;
            transition: background-color 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #0055aa;
        }
        .title-wrapper {
            background: linear-gradient(to right, #8e44ad, #3498db);
            padding: 1.2rem;
            margin-top: 2.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
        }
        .stChatMessage {
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .stChatMessage.user { background-color: #e0f7fa; }
        .stChatMessage.assistant { background-color: #f0f0f5; }
    </style>
""", unsafe_allow_html=True)

# === Header ===
st.markdown("""
<div class="title-wrapper">
    <h1>🦊 InsightFOX - API-Powered Assistant</h1>
    <p>Integrating Ollama & DuckDuckGo + FastAPI</p>
</div>
""", unsafe_allow_html=True)

# === Sidebar ===
with st.sidebar:
    st.header("⚙️ Settings")
    num_results = st.slider("📊 Number of results", 1, 10, value=3)
    chatbot_only = st.toggle("💬 Chatbot Only Mode")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown(f"<div style='text-align:center; font-size: 12px;'>📅 ©{current_year()} Present</div>", unsafe_allow_html=True)

# === Chat State ===
st.session_state.setdefault("messages", [])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === Handle Input ===
if prompt := st.chat_input("Ask me anything or search the web..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    ref_table_md = "**No references found.**"

    try:
        with st.spinner("🔍 Fetching data and generating insights..."):
            if chatbot_only:
                response = requests.get("http://localhost:8000/chat-response", params={"prompt": prompt})
                result_text = response.json().get("response", "[No output]")
            else:
                # Step 1: Search news
                search_resp = requests.post("http://localhost:8000/search-news", json={"query": prompt, "num": num_results})
                search_results = search_resp.json().get("results", [])

                # Step 2: Sort by rating
                sorted_results = sorted(
                    search_results,
                    key=lambda x: float(x.get("rating", 0)) if str(x.get("rating", "")).replace('.', '', 1).isdigit() else 0,
                    reverse=True
                )

                ref_table_md = "| # | Title | Rating | Summary |\n|---|-------|--------|---------|"
                for idx, res in enumerate(sorted_results, 1):
                    title = res.get("title", "Untitled")
                    link = res.get("link", "")
                    summary = res.get("summary", "")[:100] + "..." if len(res.get("summary", "")) > 100 else res.get("summary", "")
                    stars = rating_to_stars(res.get("rating", "N/A"))
                    title_md = f"[{title}]({link})" if link.startswith("http") else title
                    ref_table_md += f"\n| {idx} | {title_md} | {stars} | {summary} |"

                # Step 3: Generate chatbot response using top summaries
                summaries = ", ".join([res.get("summary", "") for res in sorted_results])
                final_prompt = f"User prompt: {prompt}\nContext: {summaries}"
                resp = requests.get("http://localhost:8000/chat-response", params={"prompt": final_prompt})
                result_text = resp.json().get("response", "[No response generated]")

        save_to_audio(result_text)

    except Exception as e:
        result_text = f"⚠️ Error occurred: {e}"

    # === Render Assistant Response ===
    with st.chat_message("assistant"):
        st.markdown(result_text, unsafe_allow_html=True)
        st.audio("output.mp3", format="audio/mpeg", loop=True)
        with st.expander("📚 References", expanded=True):
            st.markdown(ref_table_md, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": f"{result_text}\n\n{ref_table_md}"})
