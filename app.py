import streamlit as st
from google import genai
from google.genai import types
import json
import os
import base64
import time

FILE_NAME = 'data.json'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(CURRENT_DIR, "style.css")
HTML_TEMPLATE_PATH = os.path.join(CURRENT_DIR, "chat_template.html")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def save_data(data):
    clean_data = [msg for msg in data if "Tớ đang hơi" not in msg["content"] and "Tớ bị quá tải" not in msg["content"]]
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=4)

def load_data():
    if not os.path.exists(FILE_NAME): return []
    with open(FILE_NAME, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

st.set_page_config(page_title="Piroh - Tri kỷ ảo", page_icon="🧸", layout="wide")

try:
    img_base64 = get_base64_of_bin_file("pirohanuianh.jpg")
    bg_style = f"background-image: url('data:image/jpeg;base64,{img_base64}'); background-size: cover; background-position: center;"
    st.markdown(f"<style>.stApp {{ {bg_style} }}</style>", unsafe_allow_html=True)
except: pass

if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

API_KEY = os.environ.get("")

if "messages" not in st.session_state: st.session_state.messages = load_data()

col1, col2 = st.columns([1.2, 1])
with col1: st.markdown('<div class="left-title">PIROH</div>', unsafe_allow_html=True)
with col2:
    if st.button("Xóa chat 🗑️"):
        st.session_state.messages = []
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        st.rerun()
            
    chat_placeholder = st.empty()
    user_input = st.chat_input("Tâm sự cùng PIROH ở đây nhé...")

    def render_chat(show_typing=False, error_text=None):
        chat_html = '<div class="chat-container" id="chat-box-piro">'
        template = open(HTML_TEMPLATE_PATH, "r", encoding="utf-8").read() if os.path.exists(HTML_TEMPLATE_PATH) else ""
        
        if not st.session_state.messages:
            chat_html += template.replace("{{ role }}", "piroh").replace("{{ initial }}", "P").replace("{{ content }}", "Có chuyện gì nè, Piroh luôn ở đây lắng nghe bạn tâm sự. 🧸")
        
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "piroh"
            initial = "U" if msg["role"] == "user" else "P"
            chat_html += template.replace("{{ role }}", role).replace("{{ initial }}", initial).replace("{{ content }}", msg['content'])
        
        if show_typing:
            chat_html += '<div class="chat-row"><div class="avatar avatar-piroh">P</div><div class="message-text"><span class="typing-indicator">PIROH đang phản hồi...</span></div></div>'
        if error_text:
            chat_html += f'<div class="chat-row"><div class="avatar avatar-piroh">P</div><div class="message-text" style="font-style: italic; opacity: 0.8;">{error_text}</div></div>'
        
        chat_html += '<div id="end-of-chat"></div></div>'
        chat_placeholder.markdown(chat_html, unsafe_allow_html=True)

    render_chat()

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_chat(show_typing=True)
        
        try:
            client = genai.Client(api_key=API_KEY)
            history = [types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part.from_text(text=m["content"])]) for m in st.session_state.messages[:-1]]
            chat = client.chats.create(model="gemini-1.5-flash", history=history)
            
            response = None
            for _ in range(3):
                try:
                    response = chat.send_message(user_input)
                    break
                except Exception as e:
                    if "429" in str(e): time.sleep(2)
                    else: raise e
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            save_data(st.session_state.messages)
            st.rerun()
        except:
            if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()
            render_chat(show_typing=False, error_text="Tớ bị quá tải một chút, cậu đợi một xíu rồi nhắn lại cho tớ nha! 🧸")
