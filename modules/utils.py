import streamlit as st
import base64

def font_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def inject_fonts():
    # jalnan2_font = font_to_base64("assets/Jalnan2TTF.ttf")
    jalnan_gothic_font = font_to_base64("assets/JalnanGothicTTF.ttf")

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'JalnanGothic';
            src: url(data:font/ttf;base64,{jalnan_gothic_font}) format('truetype');
            font-weight: 400;
        }}
        
        /* 사이드바를 제외한 모든 엘리먼트에 JalnanGothic 폰트 적용 */
        div.st-emotion-cache-121p2j2.e1fqkh3o1 > div:not([data-testid="stSidebar"]) * {{
            font-family: 'JalnanGothic', sans-serif !important;
        }}
        
        </style>
    """, unsafe_allow_html=True)