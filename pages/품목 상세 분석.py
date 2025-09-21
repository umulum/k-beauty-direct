import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
from modules.utils import inject_fonts

inject_fonts() # 폰트 설정

st.set_page_config(page_title="품목 상세 분석", layout="wide")

product_options = {
    "330410": "입술화장품 (립스틱 등)",
    "330420": "눈화장용 (아이섀도 등)",
    "330430": "매니큐어/페디큐어용 (네일 에나멜 등)",
    "330491": "페이스파우다, 베이비파우다, 탈쿰파우다 등 (가루형태)",
    "330499": "기초·미용·메이크업·어린이용·선크림 등 (가루형태 제외)"
}
product_code = st.session_state.get("selected_product", "330410")
product_name = product_options[product_code]

st.title(f"📊 화장품 품목 상세 분석")

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

# 조회 기준 설정
available_periods = pd.date_range(start="2025-01-01", end="2025-07-01", freq="MS")  
available_periods = sorted(available_periods, reverse=True)
default_period = available_periods[0]

# URL 파라미터에서 값 가져오기 또는 기본값 설정
# product_code = st.query_params.get("product", "330410")
period_str = st.query_params.get("period", default_period.strftime("%Y-%m-01"))

try:
    selected_period = pd.to_datetime(period_str)
    if selected_period not in available_periods:
        selected_period = default_period
except:
    selected_period = default_period

if product_code not in product_options:
    product_code = "330410"

c1, c2 = st.columns(2)

# 변경사항을 추적할 변수
needs_rerun = False

with c1:
    product_keys = list(product_options.keys())
    current_product_index = product_keys.index(product_code)
    
    new_product = st.selectbox(
        "품목 선택",
        options=product_keys,
        index=current_product_index,
        format_func=lambda x: product_options[x],
        key="product_selector"  # 고유 키 추가
    )
    
    # 품목이 변경되면 session_state 업데이트하고 페이지 새로고침
    if new_product != product_code:
        st.session_state["selected_product"] = new_product
        st.rerun()

with c2:
    current_period_index = list(available_periods).index(selected_period)
    
    new_period = st.selectbox(
        "조회 기준 연월",
        options=available_periods,
        index=current_period_index,
        format_func=lambda x: x.strftime("%Y년 %m월")
    )
    
    # 기간이 변경되면 플래그 설정
    if new_period != selected_period:
        st.query_params.update({
            "product": product_code,
            "period": new_period.strftime("%Y-%m-01")
        })
        needs_rerun = True

# 변경사항이 있으면 여기서 재실행하고 함수 종료
if needs_rerun:
    st.rerun()
    st.stop()  # 이후 코드 실행 방지

df = data[str(product_code)]
df["기준연월"] = pd.to_datetime(df["조회기준"])
df["수출금액 (천$)"] = df["수출금액 ($)"]/1000

# 데이터 필터링 (상위 10개)
filtered = df[df["기준연월"] == selected_period].nsmallest(10, "순위")

# 좌표 join
merged = pd.merge(filtered, country_coords, on="국가명", how="left")

# Path Map 그리기 (서울 ↔ 국가)
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780

# PathLayer
path_data = []
for _, row in merged.iterrows():
    path_data.append({
        "country": row["국가명"],
        "export_value": row["수출금액 ($)"],
        "export_value_str": f"{row['수출금액 ($)']:,.0f}",
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
    get_width=15,
    width_scale=20,
    width_min_pixels=2,
    pickable=True
)

view_state = pdk.ViewState(
    longitude=30,
    latitude=40,
    zoom=1.8,
    min_zoom=1.8,   
    max_zoom=1.8,  
    pitch=0,
    bearing=0,
    drag_rotate=False,   # 지도 회전 X
)

st.pydeck_chart(pdk.Deck(
    layers=[path_layer],
    initial_view_state=view_state,
    tooltip={"text": "국가: {country}\n수출금액 ($): {export_value_str}"}
))

# 1. 한국 → 전세계 수출금액 추이
df_total = df.groupby("기준연월", as_index=False)["수출금액 (천$)"].sum()

chart1 = (
    alt.Chart(df_total)
    .mark_area(color="steelblue", opacity=0.4)
    .encode(
        x=alt.X("yearmonth(기준연월):T", title="기간", axis=alt.Axis(format="%Y년 %m월")),
        y=alt.Y("sum(수출금액 (천$)):Q", title="수출금액 (천$)", axis=alt.Axis(format="~s"), 
                scale=alt.Scale(domain=[df_total["수출금액 (천$)"].min() - 2000, df_total["수출금액 (천$)"].max() + 2000])),
        tooltip=["기준연월:T", "수출금액 (천$):Q"]
    )
    .properties(width=400, height=400)
    .configure_axis(
        labelFont="JalnanGothic",
        titleFont="JalnanGothic"
    )
    .configure_legend(
        labelFont="JalnanGothic",
        titleFont="JalnanGothic"
    )
    .configure_title(
        font="JalnanGothic"
    )
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
    ).properties(width=400, height=400)
    .configure_axis(
        labelFont="JalnanGothic",
        titleFont="JalnanGothic"
    )
    .configure_legend(
        labelFont="JalnanGothic",
        titleFont="JalnanGothic"
    )
    .configure_title(
        font="JalnanGothic"
    )
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 한국 → 전세계 수출금액 추이")
    st.altair_chart(chart1, use_container_width=True)

with col2:
    st.markdown("### 교역 지역 TOP 5")
    st.altair_chart(bar_chart, use_container_width=True)

with col3:
    st.markdown("### 전월 대비 교역 증가 TOP 5")
    st.markdown(" ")

    df_sorted = df.sort_values("기준연월")
    df_sorted['증감률'] = df_sorted['수출 증감률']*100

    period_range = pd.date_range(start=selected_period - pd.DateOffset(months=4), end=selected_period, freq="MS")

    df_recent = df_sorted[(df_sorted["기준연월"] >= period_range.min()) & (df_sorted["기준연월"] <= period_range.max())]

    # 최근 5개월 동안 데이터가 모두 있는 국가만 필터링
    valid_countries = df_recent.groupby("국가명")["기준연월"].nunique().loc[lambda x: x == 5].index

    df_recent_valid = df_recent[df_recent["국가명"].isin(valid_countries)]
    df_selected = df_recent_valid[df_recent_valid["기준연월"] == selected_period].dropna(subset=["증감률"])
    df_growth_top5 = df_selected.nlargest(5, "증감률")

    # 국가별 반복 출력
    for _, row in enumerate(df_growth_top5.itertuples(), start=1):
        country = row.국가명
        latest_growth = row.증감률

        df_country = df_recent_valid[df_recent_valid["국가명"] == country]

        chart = (
            alt.Chart(df_country)
            .mark_line(point=True)
            .encode(
                x=alt.X("yearmonth(기준연월):T", title=None),
                y=alt.Y("증감률:Q", title=None),
                tooltip=[
                    alt.Tooltip("기준연월:T", title="기간"),
                    alt.Tooltip("증감률:Q", format=".2f", title="수출 증감률 (%)")
                ]
            )
            .properties(width=200, height=50)
            .configure_axis(
                grid=False,    # 격자선 제거
                domain=False,  # 축 선 제거
                ticks=False,   # 눈금 제거
                labels=False   # 레이블 제거
            )
        )

        col1, col2, col3, col4 = st.columns([0.5, 2, 2, 1.5])
        with col1:
            st.markdown(" ")
        with col2:
            st.markdown(f"**{country}**")
        with col3:
            st.altair_chart(chart, use_container_width=True)
        with col4:
            st.markdown(f"{latest_growth:.2f}%")            

# 데이터 표
st.subheader(f"📑 {product_options[product_code]} 상위 10개국 ({selected_period.strftime('%Y년 %m월')})")
st.dataframe(filtered[["순위", "국가명", "수출금액 ($)", "수출 점유율", "수출 증감률"]], hide_index=True)
