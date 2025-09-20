import streamlit as st
import pandas as pd
import altair as alt
from recommender import initialize_recommender_system, recommend_countries
from utils import inject_fonts

inject_fonts() # 폰트 설정

st.set_page_config(page_title="화장품 수출 추천 서비스", layout="wide")

st.title("💄 화장품 수출 국가 추천 서비스")

st.subheader("분석할 화장품 품목")

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
        label_visibility="collapsed"  # 위쪽 라벨 숨김 
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

st.subheader("화장품 트렌드 국가 추천 시스템")
st.markdown("관심 있는 화장품 키워드를 입력하면 관련 트렌드가 높은 국가를 추천해드립니다!")


country_names = {
    'usa': '미국',
    'uae': '아랍에미리트',
    'vietnam': '베트남',
    'brazil': '브라질',
    'france': '프랑스',
    'uk': '영국',
    'india': '인도',
    'japan': '일본',
    'indonesia': '인도네시아',
    'turkey': '튀르키예',
    'thailand': '태국',
    'china': '중국'
}

st.markdown("**추천 국가:** " + ", ".join(country_names.values()))

# 추천 시스템 초기화 (캐시됨)
@st.cache_data
def get_recommender_data():
    return initialize_recommender_system()

if "recommender_data" not in st.session_state:
    with st.spinner('추천 시스템 초기화 중...'):
        st.session_state.recommender_data = initialize_recommender_system()

recommender_data = st.session_state.recommender_data

# st.success("✅ 시스템 초기화 완료!")

# 사용자 입력
if "keywords_input" not in st.session_state:
    st.session_state.keywords_input = ""

col1, col2 = st.columns([3, 1])

with col1:
    keywords_input = st.text_input(
        "키워드 입력",
        value=st.session_state.keywords_input,
        placeholder="예: vegan, organic, skincare, 비건, 유기농, 스킨케어",
    )
    st.session_state.keywords_input = keywords_input
with col2:
    top_n = st.selectbox("추천 국가 수:", [3, 5], index=0)

# 추천 실행
if keywords_input:
    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
    
    if keywords:
        with st.spinner('국가를 추천하는 중...'):
            try:
                recommendations = recommend_countries(
                    keywords,
                    recommender_data['tfidf_transformer'],
                    recommender_data['tfidf_matrix'],
                    recommender_data['counts_df'],
                    recommender_data['model'],
                    recommender_data['keyword_embeddings'],
                    top_n=top_n,
                    return_scores=True
                )
                
                recommendations = [(country, score) for country, score in recommendations if score > 0]

                if recommendations:
                    st.markdown(f"#### 🎯 '{', '.join(keywords)}' 키워드 기반 추천 국가")
                    
                    # 추천 결과를 3열로 표시
                    cols = st.columns(min(3, len(recommendations)))
                    
                    for i, (country, score) in enumerate(recommendations):
                        with cols[i % 3]:
                            
                            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem;">
                                <div>
                                    <div style="font-size: 0.875rem; color: #666;">#{i+1} {country.upper()} {score:.3f}</div>
                                    <div style="font-size: 1.25rem; font-weight: 600;">{country_names[country]}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            if st.button(f"📊 {country_names[country]} 상세 보기", key=f"detail_{country}_{i}", use_container_width=True):
                                st.session_state.selected_country = country_names[country]
                                st.switch_page("pages/country.py")
                else:
                    st.warning("⚠️ 입력하신 키워드와 매칭되는 결과가 없습니다. 다른 키워드를 시도해보세요.")
                    
            except Exception as e:
                st.error(f"❌ 추천 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("키워드를 입력해주세요.")
st.markdown("----")

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