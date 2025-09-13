import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="품목 상세", layout="wide")

st.title("📊 품목 상세 페이지")

product_options = {
    "330410": "입술화장품 (립스틱 등)",
    "330420": "눈화장용 (아이섀도 등)",
    "330430": "매니큐어/페디큐어용 (네일 에나멜 등)",
    "330491": "페이스파우다, 베이비파우다, 탈쿰파우다 등 (가루형태)",
    "330499": "기초·미용·메이크업·어린이용·선크림 등 (가루형태 제외)"
}

product_code = st.session_state.get("selected_product", "330410")
product_name = product_options[product_code]

st.subheader(f"품목명: {product_name}")
st.write(f"선택한 품목 코드: {product_code}")

# -------------------------------
# 🔹 캐시된 데이터 로딩 함수
# -------------------------------
@st.cache_data
def load_excel(file_path: str):
    xls = pd.ExcelFile(file_path)
    data_dict = {}
    for sheet in xls.sheet_names:
        data_dict[sheet] = pd.read_excel(file_path, sheet_name=sheet)
    return data_dict

excel_file = "data/화장품 수출입.xlsx"
data = load_excel(excel_file)
country_coords = data["lat-lon"]

df = data[str(product_code)]

# -------------------------------
# 🔹 조회 기준 선택 (기본: 가장 최근)
# -------------------------------
available_periods = sorted(df["조회기준"].unique(), reverse=True)
default_period = available_periods[0]

selected_period = st.selectbox(
    "조회 기준 (연-월)", 
    options=available_periods, 
    index=0
)

# -------------------------------
# 🔹 데이터 필터링 (상위 10개)
# -------------------------------
filtered = df[df["조회기준"] == selected_period].nsmallest(10, "순위")

# 좌표 join
merged = pd.merge(filtered, country_coords, on="국가명", how="left")

# -------------------------------
# 🔹 Path Map 그리기 (서울 ↔ 국가)
# -------------------------------
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780

# PathLayer는 "path" 컬럼을 요구함
path_data = []
for _, row in merged.iterrows():
    path_data.append({
        "country": row["국가명"],
        "export_value": row["수출금액 ($)"],
        "path": [
            [SEOUL_LON, SEOUL_LAT],   # 출발 (서울)
            [row["경도"], row["위도"]]  # 도착 (국가)
        ]
    })

path_layer = pdk.Layer(
    "PathLayer",
    data=path_data,
    get_path="path",
    get_color=[0, 128, 255],
    get_width=2,
    width_scale=20,
    width_min_pixels=2,
    pickable=True
)

view_state = pdk.ViewState(
    latitude=30,
    longitude=20,
    zoom=1.2,
    pitch=0
)

st.pydeck_chart(pdk.Deck(
    layers=[path_layer],
    initial_view_state=view_state,
    tooltip={"text": "국가: {country}\n수출금액: {export_value}"}
))

# -------------------------------
# 🔹 표로 데이터도 같이 보여주기
# -------------------------------
st.subheader(f"📑 {product_name} 상위 10개국 ({selected_period})")
st.dataframe(filtered[["순위", "국가명", "수출금액 ($)", "수출 점유율"]])
