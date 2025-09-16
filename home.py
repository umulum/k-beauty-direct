import streamlit as st
import pandas as pd
import altair as alt


st.set_page_config(page_title="화장품 수출 추천 서비스", layout="wide")

st.title("💄 화장품 수출 국가 추천 서비스")
st.subheader("분석할 화장품 품목을 선택하세요.")

# 품목 옵션
product_options = {
    "330410": "입술화장품 (립스틱 등)",
    "330420": "눈화장용 (아이섀도 등)",
    "330430": "매니큐어/페디큐어용 (네일 에나멜 등)",
    "330491": "페이스파우다, 베이비파우다, 탈쿰파우다 등 (가루형태)",
    "330499": "기초·미용·메이크업·어린이용·선크림 등 (가루형태 제외)"
}

col1, col2 = st.columns([4, 1])  

with col1:
    selected_key = st.selectbox(
        "품목 선택",
        options=[""] + list(product_options.keys()),
        format_func=lambda x: product_options.get(x, "품목을 선택하세요") if x else "--- 품목을 선택하세요 ---",
        label_visibility="collapsed"  # 위쪽 라벨 숨김 (필요하면 제거)
    )

with col2:
    if st.button("조회하기"):
        if selected_key:
            st.session_state["selected_product"] = selected_key
        else:
            # 선택 안 한 경우 → 기본값 330410
            st.session_state["selected_product"] = "330410"
        st.switch_page("pages/products.py")

st.markdown("----")
# --------------------------------
# KOTRA 공공데이터 국가별 수출금액 시각화 
# --------------------------------

# CSV 로드
df_cos = pd.read_csv("data/대한무역투자진흥공사_4대 소비재 국가별 수출금액 (화장품)_20221231.csv")

# 전체 합계
df_total = df_cos.drop(columns=["국가명"]).sum().reset_index()
df_total.columns = ["연도", "수출금액"]
df_total["국가명"] = "전체 합계"

key_countries = ["미국", "중국", "일본"]
df_key = df_cos[df_cos["국가명"].isin(key_countries)]
df_key = df_key.melt(id_vars="국가명", var_name="연도", value_name="수출금액")

df_plot = pd.concat([df_total, df_key], ignore_index=True)

df_plot["수출금액($)"] = df_plot["수출금액"]  # / 1_000_000

# 꺾은선 그래프
line_chart = alt.Chart(df_plot).mark_line(point=True).encode(
    x=alt.X("연도:N", axis=alt.Axis(title="연도")),
    y=alt.Y("수출금액($):Q",
            axis=alt.Axis(title="수출금액 ($)", format=",.0f")),  # 천단위 구분, 소수점 제거
    color="국가명:N",
    tooltip=["국가명", "연도", alt.Tooltip("수출금액($):Q", format=",.2f")]
).properties(
    width=700,
    height=400,
    title="화장품 수출 성장 추이"
)

st.altair_chart(line_chart, use_container_width=True)

# --------------------------------
# 한국무역통계포털 수출입 통계 시각화 
# --------------------------------

@st.cache_data
def load_excel(file_path: str):
    xls = pd.ExcelFile(file_path)
    data_list = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        df["국가"] = sheet  # 시트명이 곧 국가명
        data_list.append(df)
    return pd.concat(data_list, ignore_index=True)

excel_file = "data/한국무역통계포털 3304 수출입.xlsx"  # 파일 경로 수정
df = load_excel(excel_file)

col1, col2 = st.columns(2)

with col1:
    export_chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("기간:N", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("수출 금액:Q", axis=alt.Axis(title="수출 금액 ($)")),
        color="국가:N",
        tooltip=["국가", "기간", "수출 금액"]
    ).properties(
        width=600,
        height=400,
        title="수출 금액 변화"
    )
    st.altair_chart(export_chart, use_container_width=True)

with col2:
    import_chart = alt.Chart(df[df["국가"] != "한국"]).mark_line(point=True).encode(
        x=alt.X("기간:N", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("수입 금액:Q", axis=alt.Axis(title="수입 금액 ($)")),
        color="국가:N",
        tooltip=["국가", "기간", "수입 금액"]
    ).properties(
        width=600,
        height=400,
        title="수입 금액 변화"
    )
    st.altair_chart(import_chart, use_container_width=True)