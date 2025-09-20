from pathlib import Path
import base64
import streamlit as st

# 루트 경로 = modules의 상위 폴더(K-Beauty Direct)
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

def font_to_base64(filename: str) -> str:
    path = ASSETS_DIR / filename   # 여기서는 "JalnanGothicTTF.ttf" 만 넣기
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def inject_fonts():
    jalnan_gothic_font = font_to_base64("JalnanGothicTTF.ttf")

    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'JalnanGothic';
            src: url(data:font/ttf;base64,{jalnan_gothic_font}) format('truetype');
            font-weight: 400;
        }}

        main, [role="main"], div[role="main"], section[data-testid="stAppViewContainer"], .block-container {{
            font-family: 'JalnanGothic', sans-serif !important;
        }}

        h1, h2, h3, h4, h5, h6, p {{
            font-family: 'JalnanGothic', sans-serif !important;
        }}

        /* 사이드바 아이콘만 Source Sans Pro 적용 */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] svg, 
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span {{
            font-family: 'Source Sans Pro', sans-serif !important;
        }}

        </style>
    """, unsafe_allow_html=True)
