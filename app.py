import streamlit as st
from google import genai
from google.genai import types
import json
import os
import base64

# Cấu hình file
FILE_NAME = 'data.json'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(CURRENT_DIR, "style.css")
HTML_TEMPLATE_PATH = os.path.join(CURRENT_DIR, "chat_template.html")

# Lấy API Key từ Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Chưa thiết lập GEMINI_API_KEY trong Secrets!")
    st.stop()

def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file): return ""
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def save_data(data):
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    if not os.path.exists(FILE_NAME): return []
    with open(FILE_NAME, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

st.set_page_config(page_title="Piroh - Tri kỷ ảo", page_icon="🧸", layout="wide")

# CSS Background
try:
    img_base64 = get_base64_of_bin_file("pirohanuianh.jpg")
    if img_base64:
        bg_style = f"background-image: url('data:image/jpeg;base64,{img_base64}'); background-size: cover; background-position: center;"
        st.markdown(f"<style>.stApp {{ {bg_style} }}</style>", unsafe_allow_html=True)
except: pass

if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = load_data()

col1, col2 = st.columns([1.2, 1])
with col1: st.markdown('<div class="left-title">PIROH</div>', unsafe_allow_html=True)
with col2:
    if st.button("Xóa chat 🗑️"):
        st.session_state.messages = []
        if os.path.exists(FILE_NAME): os.remove(FILE_NAME)
        st.rerun()
            
    chat_placeholder = st.empty()

    def render_chat(show_typing=False, error_text=None):
        template = ""
        if os.path.exists(HTML_TEMPLATE_PATH):
            with open(HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template = f.read()
        
        chat_html = '<div class="chat-container" id="chat-box-piro">'
        
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
        chat_placeholder.markdown(chat_html, unsafe_html=True)

    render_chat()

    user_input = st.chat_input("Tâm sự cùng PIROH ở đây nhé...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_chat(show_typing=True)
        
        try:
            client = genai.Client(api_key=API_KEY)
            history = [types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part.from_text(text=m["content"])]) for m in st.session_state.messages[:-1]]
            chat = client.chats.create(model="gemini-1.5-flash", history=history)
            
            response = chat.send_message(user_input)
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            save_data(st.session_state.messages)
            st.rerun()
        except Exception as e:
            render_chat(show_typing=False, error_text="Tớ bị quá tải một chút, cậu đợi một xíu rồi nhắn lại cho tớ nha! 🧸")
