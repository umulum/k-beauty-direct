# import streamlit as st
# import pydeck as pdk
# import pandas as pd

# # 예시 데이터 (한국 -> 미국, 한국 -> 프랑스)
# data = pd.DataFrame([
#     {"from_lat": 37.5665, "from_lon": 126.9780, "to_lat": 40.7128, "to_lon": -74.0060, "trade": "export"},  # 서울→뉴욕
#     {"from_lat": 37.5665, "from_lon": 126.9780, "to_lat": 48.8566, "to_lon": 2.3522, "trade": "import"}    # 서울→파리
# ])

# arc_layer = pdk.Layer(
#     "ArcLayer",
#     data,
#     get_source_position=["from_lon", "from_lat"],
#     get_target_position=["to_lon", "to_lat"],
#     get_source_color=[0, 128, 255],   # 시작 색상
#     get_target_color=[255, 0, 0],     # 끝 색상
#     get_width=3,
#     auto_highlight=True,
#     pickable=True,
# )

# view_state = pdk.ViewState(
#     latitude=30, longitude=20, zoom=1.2, bearing=0, pitch=30
# )

# st.pydeck_chart(pdk.Deck(
#     layers=[arc_layer],
#     initial_view_state=view_state,
#     tooltip={"text": "경로: {trade}"}
# ))


# import streamlit as st
# import base64

# def local_font(path, name, weight=400):
#     with open(path, "rb") as f:
#         data = f.read()
#     b64 = base64.b64encode(data).decode()
#     return f"""
#     @font-face {{
#         font-family: '{name}';
#         src: url(data:font/ttf;base64,{b64}) format('truetype');
#         font-weight: {weight};
#     }}
#     """

# css = """
# <style>
# {jalnan2}
# {jalnan_gothic}
# body, html, [class*="css"] {{
#     font-family: 'Jalnan2', sans-serif;
# }}
# </style>
# """.format(
#     jalnan2=local_font("assets/Jalnan2TTF.ttf", "Jalnan2", 400),
#     jalnan_gothic=local_font("assets/JalnanGothicTTF.ttf", "JalnanGothic", 400),
# )

# st.markdown(css, unsafe_allow_html=True)

# st.markdown('<p style="font-family:Jalnan2; font-size:24px;">✅ Jalnan2 적용됨</p>', unsafe_allow_html=True)
# st.markdown('<p style="font-family:JalnanGothic; font-size:24px;">✅ JalnanGothic 적용됨</p>', unsafe_allow_html=True)

import streamlit as st
import base64

# base64 인코딩 함수
def font_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# 폰트 파일 경로
jalnan2_font = font_to_base64("assets/Jalnan2TTF.ttf")
jalnan_gothic_font = font_to_base64("assets/JalnanGothicTTF.ttf")

# CSS 삽입
st.markdown(f"""
    <style>
    @font-face {{
        font-family: 'Jalnan2';
        src: url(data:font/ttf;base64,{jalnan2_font}) format('truetype');
        font-weight: 400;
    }}
    @font-face {{
        font-family: 'JalnanGothic';
        src: url(data:font/ttf;base64,{jalnan_gothic_font}) format('truetype');
        font-weight: 400;
    }}
    html, body, [class*="css"] {{
        font-family: 'Jalnan2', sans-serif;
        font-weight: 400;
    }}
    </style>
""", unsafe_allow_html=True)

# 테스트
st.markdown('<p style="font-family:Jalnan2; font-size:24px;">잘난2 폰트 적용</p>', unsafe_allow_html=True)
st.markdown('<p style="font-family:JalnanGothic; font-size:24px;">잘난고딕 폰트 적용</p>', unsafe_allow_html=True)
st.markdown('''
<p style="font-size:22px;">
  <span style="font-family:Jalnan2; color:#e74c3c;">잘난2</span>와 
  <span style="font-family:JalnanGothic; color:#2980b9;">잘난고딕</span>을 
  한 문장에 섞어서 사용!
</p>
''', unsafe_allow_html=True)