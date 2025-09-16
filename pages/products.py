import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

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

# 캐시된 데이터 로딩 함수
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

df["기준연월"] = pd.to_datetime(df["조회기준"])
df["수출금액 (천$)"] = df["수출금액 ($)"]/1000

# 조회 기준 선택 
available_periods = sorted(df["기준연월"].unique(), reverse=True)
default_period = available_periods[0]

selected_period = st.selectbox(
    "조회 기준 연월",
    options=available_periods,
    index=0,
    format_func=lambda x: x.strftime("%Y년 %m월")  # 표시용 포맷
)

# 데이터 필터링 (상위 10개)
filtered = df[df["기준연월"] == selected_period].nsmallest(10, "순위")

# 좌표 join
merged = pd.merge(filtered, country_coords, on="국가명", how="left")

# Path Map 그리기 (서울 ↔ 국가)-
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

# 1. 한국 → 전세계 수출금액 추이
df_total = df.groupby("기준연월", as_index=False)["수출금액 (천$)"].sum()

chart1 = (
    alt.Chart(df_total)
    .mark_area(color="steelblue", opacity=0.4)
    .encode(
        x=alt.X("yearmonth(기준연월):T", title="기간", axis=alt.Axis(format="%Y년 %m월")),
        y=alt.Y("sum(수출금액 (천$)):Q", title="수출금액 (천$)", axis=alt.Axis(format="~s"), 
                scale=alt.Scale(domain=[45000, 60000])),
        tooltip=["기준연월:T", "수출금액 (천$):Q"]
    )
    .properties(width=400, height=400, title="한국 → 전세계 수출금액 추이")
)

# 2. 교역지역 TOP 5
df_top5 = filtered.nlargest(5, "수출금액 (천$)")

bar_chart = (
    alt.Chart(df_top5)
    .mark_bar(color="orange")
    .encode(
        x=alt.X("수출금액 (천$):Q", axis=alt.Axis(format="~s"), title="수출금액 (천$)"),
        y=alt.Y("국가명:N", sort="-x", title="국가"),
        tooltip=["국가명", "수출금액 (천$)"]
    ).properties(
    width=400,
    height=400,
    title="교역지역 TOP 5"
)
)

# -------------------------------
# 3. 전월 대비 교역 증가 TOP 5
# -------------------------------
df_sorted = df.sort_values("기준연월")
df_sorted["전월수출"] = df_sorted.groupby("국가명")["수출금액 ($)"].shift(1)
df_sorted["증감률"] = (df_sorted["수출금액 ($)"] - df_sorted["전월수출"]) / df_sorted["전월수출"] * 100

df_growth = df_sorted[df_sorted["기준연월"] == selected_period].dropna(subset=["증감률"])
df_growth_top5 = df_growth.nlargest(5, "증감률")

# 미니 라인차트용: 최근 4개월
df_recent = df_sorted[df_sorted["기준연월"] >= (selected_period - pd.DateOffset(months=4))]

line_chart_growth = (
    alt.Chart(df_recent[df_recent["국가명"].isin(df_growth_top5["국가명"])])
    .mark_line(point=True)
    .encode(
        x=alt.X("yearmonth(기준연월):T", title="기간"),
        y=alt.Y("수출금액 ($):Q", axis=alt.Axis(format="~s")),
        color="국가명:N",
        tooltip=["국가명", "기준연월:T", "수출금액 ($)"]
    )
    .properties(width=400, height=400, title="전월대비 교역증가 TOP 5")
)

# -------------------------------
# 레이아웃 (열 3개)
# -------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.altair_chart(chart1, use_container_width=True)

with col2:
    st.altair_chart(bar_chart, use_container_width=True)

with col3:
    st.altair_chart(line_chart_growth, use_container_width=True)

# 데이터 표
st.subheader(f"📑 {product_name} 상위 10개국 ({selected_period.strftime('%Y년 %m월')})")
st.dataframe(filtered[["순위", "국가명", "수출금액 ($)", "수출 점유율"]])
