# chatbot_clean.py
"""
Simple Persona ChatBot using Streamlit and OpenAI API v1.0+

Features:
- Personas: RoastBot, ShakespeareBot, EmojiBot
- Maintains chat history in session (optional disk save)
- Chat export to JSON, clear history, debug raw messages
- Uses OpenAI's latest chat API
"""

import os
import json
import time
from typing import List, Dict, Any

import streamlit as st
from openai import OpenAI

# -------- Configuration --------
APP_TITLE = "Persona ChatBot — Roast / Shakespeare / Emoji"
PERSIST_FILE = "chat_history.json"
DEFAULT_MODEL = "gpt-3.5-turbo"

# -------- Personas --------
PERSONAS = {
    "RoastBot": {
        "name": "RoastBot",
        "system": (
            "You are RoastBot. Give short, witty, playful roasts. "
            "If user asks for serious info, give it with a mild sarcastic touch."
        ),
    },
    "ShakespeareBot": {
        "name": "ShakespeareBot",
        "system": (
            "You are ShakespeareBot. Reply in Early Modern English style. "
            "Use 'thee', 'thou', poetic phrasing, and a formal tone."
        ),
    },
    "EmojiBot": {
        "name": "EmojiBot",
        "system": (
            "You are EmojiBot. Translate messages mostly into emojis. "
            "You can add a short English note in parentheses if needed."
        ),
    },
}

# -------- Utility Functions --------
def save_history(history: List[Dict[str, Any]], filename: str = PERSIST_FILE):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"saved_at": time.time(), "history": history}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Could not save chat: {e}")

def load_history(filename: str = PERSIST_FILE) -> List[Dict[str, Any]]:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("history", [])
    except Exception as e:
        st.warning(f"Could not load chat: {e}")
        return []

def append_message(history: List[Dict[str, Any]], role: str, text: str):
    history.append({"role": role, "text": text, "ts": time.time()})

def render_chat(history: List[Dict[str, Any]], persona_name: str):
    if not history:
        st.info("No messages yet. Type something below to start!")
        return
    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg.get("ts", 0)))
        if role == "user":
            st.markdown(f"**You**  <span style='color:gray;font-size:0.8rem'>· {ts}</span>", unsafe_allow_html=True)
            st.write(text)
        else:
            st.markdown(f"**{persona_name}**  <span style='color:gray;font-size:0.8rem'>· {ts}</span>", unsafe_allow_html=True)
            st.write(text)
        st.markdown("---")

# -------- Streamlit UI Setup --------
st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="centered")
st.title(APP_TITLE)
st.markdown("Chat with different personas. Make sure your OpenAI API key is set (`OPENAI_API_KEY`).")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    model = st.selectbox("Model", [DEFAULT_MODEL, "gpt-4"])
    temperature = st.slider("Temperature", 0.0, 1.0, 0.65, 0.05)
    max_tokens = st.slider("Max tokens", 64, 1024, 512, 64)
    persist_to_disk = st.checkbox("Save chat to disk", value=False)
    show_raw = st.checkbox("Show raw JSON (debug)", value=False)

# Select persona
persona_key = st.selectbox("Persona", list(PERSONAS.keys()))
persona = PERSONAS[persona_key]
st.markdown(f"**Active Persona:** {persona['name']}")
st.caption(persona["system"])

# Initialize session chat history
if "history" not in st.session_state:
    st.session_state.history = load_history(PERSIST_FILE) if persist_to_disk else []

# Show chat history
st.subheader("Conversation")
render_chat(st.session_state.history, persona['name'])
if show_raw:
    st.json(st.session_state.history)

# Chat input and buttons
st.text_input("Type your message:", key="user_input", placeholder="Say something...")
col1, col2, col3 = st.columns([1,1,1])
with col1:
    send = st.button("Send")
with col2:
    clear = st.button("Clear History")
with col3:
    export = st.button("Export JSON")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------- Handle Send --------
if send:
    user_input = st.session_state.get("user_input", "").strip()
    if not user_input:
        st.warning("Please type a message!")
    else:
        try:
            append_message(st.session_state.history, "user", user_input)

            # Prepare messages for API
            messages = [{"role": "system", "content": persona["system"]}]
            for h in st.session_state.history[-24:]:
                messages.append({"role": h["role"], "content": h["text"]})

            # Call OpenAI chat API
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            ai_text = response.choices[0].message.content.strip()
            append_message(st.session_state.history, "assistant", ai_text)

            if persist_to_disk:
                save_history(st.session_state.history)

            st.rerun()

        except Exception as e:
            st.error(f"Error generating response: {e}")

# -------- Handle Clear History --------
if clear:
    st.session_state.history = []
    if persist_to_disk and os.path.exists(PERSIST_FILE):
        os.remove(PERSIST_FILE)
    st.success("Chat cleared.")
    st.rerun()

# -------- Handle Export --------
if export:
    export_data = {
        "exported_at": time.time(),
        "persona": persona_key,
        "model": model,
        "history": st.session_state.history,
    }
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    st.download_button("Download JSON", data=json_str, file_name="conversation_export.json", mime="application/json")

# Example prompts
with st.expander("Example prompts"):
    st.write("- Tell me a joke about programming.")
    st.write("- Explain the Pythagorean theorem simply.")
    st.write("- Convert 'I love pizza' into emojis.")
    st.write("- Roast me gently for forgetting my keys.")
    st.write("- Write a short Shakespearean insult.")

st.markdown("---")
st.caption("Made with Streamlit. Keep your API key safe for production.")
