import streamlit as st
import pydeck as pdk
import pandas as pd

# 예시 데이터 (한국 -> 미국, 한국 -> 프랑스)
data = pd.DataFrame([
    {"from_lat": 37.5665, "from_lon": 126.9780, "to_lat": 40.7128, "to_lon": -74.0060, "trade": "export"},  # 서울→뉴욕
    {"from_lat": 37.5665, "from_lon": 126.9780, "to_lat": 48.8566, "to_lon": 2.3522, "trade": "import"}    # 서울→파리
])

arc_layer = pdk.Layer(
    "ArcLayer",
    data,
    get_source_position=["from_lon", "from_lat"],
    get_target_position=["to_lon", "to_lat"],
    get_source_color=[0, 128, 255],   # 시작 색상
    get_target_color=[255, 0, 0],     # 끝 색상
    get_width=3,
    auto_highlight=True,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=30, longitude=20, zoom=1.2, bearing=0, pitch=30
)

st.pydeck_chart(pdk.Deck(
    layers=[arc_layer],
    initial_view_state=view_state,
    tooltip={"text": "경로: {trade}"}
))
