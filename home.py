import streamlit as st

st.set_page_config(page_title="화장품 수출 추천 서비스", layout="wide")

st.title("💄 화장품 수출 국가 추천 서비스")
st.write("분석할 화장품 품목을 선택하세요.")

# 품목 옵션
product_options = {
    "330410": "입술화장품 (립스틱 등)",
    "330420": "눈화장용 (아이섀도 등)",
    "330430": "매니큐어/페디큐어용 (네일 에나멜 등)",
    "330491": "페이스파우다, 베이비파우다, 탈쿰파우다 등 (가루형태)",
    "330499": "기초·미용·메이크업·어린이용·선크림 등 (가루형태 제외)"
}

# 드롭다운 (기본값: 선택 안 함)
selected_key = st.selectbox(
    "품목 선택",
    options=[""] + list(product_options.keys()),
    format_func=lambda x: product_options.get(x, "품목을 선택하세요") if x else "--- 품목을 선택하세요 ---"
)

if st.button("조회하기"):
    if selected_key:
        st.session_state["selected_product"] = selected_key
    else:
        # 선택 안 한 경우 → 기본값 330410
        st.session_state["selected_product"] = "330410"
    st.switch_page("pages/products.py")
