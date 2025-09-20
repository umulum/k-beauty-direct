import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import requests
import time
from modules.utils import inject_fonts

inject_fonts() # 폰트 설정

st.set_page_config(page_title="국가 상세 분석", layout="wide")

st.title("🌎 국가별 상세 분석")

@st.cache_data
def load_excel(path):
    trade_df = pd.read_excel(path, sheet_name="Trade Indicator")
    kpi_df = pd.read_excel(path, sheet_name="KPI")
    return trade_df, kpi_df

# n8n 웹훅 호출
@st.cache_data(ttl=3600, show_spinner=False)
def get_legal_info(country_name):
    """n8n 워크플로우를 호출하여 법률 정보를 가져오는 함수"""
    webhook_url = "http://localhost:5678/webhook/legal-info-webhook"
    payload = {"query": {"country": country_name}}

    try:
        with st.spinner(f'{country_name}의 최근 화장품 수출 관련 법률 정보를 분석 중입니다... (최대 10분 소요됩니다)'):
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=300 
            )
            response.raise_for_status()  

            if not response.text.strip():
                return "오류: n8n에서 빈 응답을 받았습니다. 워크플로우를 확인해주세요."

            data = response.json()

            if data.get('success'):
                return data.get('summary', '오류: 응답에 요약 정보가 없습니다.')
            else:
                return data.get('message', "선택한 국가의 법률 정보 데이터가 없습니다.")

    except requests.exceptions.Timeout:
        return "오류: 요청 시간이 초과되었습니다. n8n 워크플로우 실행이 너무 오래 걸립니다."
    except requests.exceptions.ConnectionError:
        return f"오류: n8n 서버에 연결할 수 없습니다. URL: {webhook_url}"
    except requests.exceptions.HTTPError as e:
        return f"서버 오류: {e.response.status_code} 응답. n8n 워크플로우 에러를 확인하세요."
    except json.JSONDecodeError:
        return f"오류: n8n 응답을 파싱할 수 없습니다. 응답 내용: {response.text[:200]}"
    except Exception as e:
        return f"알 수 없는 오류가 발생했습니다: {str(e)}"
trade_df, kpi_df = load_excel("data/국가 정보.xlsx")

countries = ["미국", "베트남", "브라질", "영국", "인도", "인도네시아",
             "일본", "중국", "태국", "튀르키예", "프랑스", "UAE"]

selected_country_name = st.session_state.get("selected_country", "미국")

selected_country = st.selectbox(
    "국가 선택",
    options=countries,
    index=countries.index(selected_country_name)
    # key="selected_country"                    
)

# 국가가 변경시 정보 초기화
if st.session_state.get("selected_country") != selected_country:
    st.session_state.selected_country = selected_country
    if 'legal_info' in st.session_state:
        del st.session_state.legal_info
    if 'legal_info_loaded' in st.session_state:
        del st.session_state.legal_info_loaded

country_code_map = {
    "미국": "US", "베트남": "VN", "브라질": "BR", "영국": "GB",
    "인도": "IN", "인도네시아": "ID", "일본": "JP", "중국": "CN",
    "태국": "TH", "튀르키예": "TR", "프랑스": "FR", "UAE": "AE"
}

img_path = os.path.join("data", "img", f"{selected_country}.jpg")
img = f"https://www.kotra.or.kr/bigdata/resources/images/nation/{country_code_map[selected_country]}.jpg"
url = f'https://www.kotra.or.kr/bigdata/marketAnalysis#search/{country_code_map[selected_country]}'

# 국기, KPI 카드
col1, col2, col3 = st.columns([0.6, 2.2, 1.2])  

with col1:
    st.markdown(
        f"""
        <a href="{url}" target="_blank">
        <img src="{img}" width="180px" style="margin:20px; padding:10px; margin-top:30px;">
        </a>
        """,
        unsafe_allow_html=True
    )

with col3:
    if os.path.exists(img_path):
        st.image(img_path)

with col2:
    kpi_row = kpi_df[kpi_df["국가"] == selected_country]

    if not kpi_row.empty:
        kpi_cols = [col for col in kpi_df.columns if col != "국가"]
        kpi_units = ["$", "건", "건", "명", "건", "백만$"]  # KPI 단위

        for i in range(0, len(kpi_cols), 3):
            row_kpi_cols = kpi_cols[i:i+3]
            row_kpi_units = kpi_units[i:i+3]
            cols = st.columns(len(row_kpi_cols))  # 남은 개수만큼 컬럼 생성

            for col, kpi_name, unit in zip(cols, row_kpi_cols, row_kpi_units):
                value = kpi_row.iloc[0][kpi_name]
                html = f"""
                    <div style="
                        text-align:center;
                        border:1px solid #ddd;
                        border-radius:8px;
                        padding:10px;
                        margin:5px;
                        background-color:#ffffff;
                    ">
                        <div style="font-size:16px;font-weight:bold;margin-bottom:5px">{kpi_name}</div>
                        <div style="font-size:24px;font-weight:bold;display:inline">{value}</div>
                        <div style="font-size:14px;color:gray;display:inline;margin-left:2px">{unit}</div>
                    </div>
                """
                col.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("선택한 국가의 KPI 데이터가 없습니다.")


# Trade Indicator 레이더 차트 
available_hscodes = [330410, 330420, 330430, 330491, 330499]
product_options = {
    "입술화장품 (립스틱 등)": 330410,
    "눈화장용 (아이섀도 등)": 330420,
    "매니큐어/페디큐어용 (네일 에나멜 등)": 330430,
    "페이스파우다, 베이비파우다, 탈쿰파우다 등 (가루형태)": 330491,
    "기초·미용·메이크업·어린이용·선크림 등 (가루형태 제외)": 330499
}
default_index = 0

col1, col2 = st.columns([1.5, 3]) 
with col1:
    dropdown_options = list(product_options.keys())
    selected_product = st.selectbox("제품 선택", dropdown_options, index=0)
    selected_hscode = product_options[selected_product]
    # selected_hscode = st.selectbox("HS CODE 선택", available_hscodes, index=default_index)
    row = trade_df[(trade_df["국가"] == selected_country) & (trade_df["HSCODE"] == selected_hscode)]
    if not row.empty:
        radar_data = row.melt(id_vars=["국가", "HSCODE"],var_name="지표",value_name="값")
        fig = px.line_polar(radar_data, r="값", theta="지표", line_close=True, hover_name="지표", hover_data={"값": True}, color_discrete_sequence=["#D6B3FF"])
        fig.update_traces(fill="toself")
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            dragmode=False  # 확대/이동 비활성화
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택한 국가와 HS CODE 데이터가 없습니다.")

with col2:
    st.markdown("-----")
    if not row.empty:
        radar_data = row.melt(id_vars=["국가", "HSCODE"],var_name="지표",value_name="값")

        for i in range(0, len(radar_data), 3):
            cols = st.columns([1, 1, 1])
            for j, (_, r) in enumerate(radar_data.iloc[i:i+3].iterrows()):
                with cols[j]:
                    st.markdown(f'#### {r["지표"]}') 
                    val = r["값"]
                    if val <= 3:
                        bar_color = "#FFA8A8"  # 연한 빨강 (파스텔)
                    elif val <= 7:
                        bar_color = "#FFF29A"  # 연한 노랑
                    else:
                        bar_color = "#A8E6CF"  # 연한 초록
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=r["값"],
                        number={'valueformat': '.1f', 'font': {'color': '#111111'}},
                        title=None,
                        gauge={
                            'axis': {'range': [0, 10], 'dtick': 11},
                            'bar': {'color': bar_color, 'thickness': 1},            
                        }
                    ))
                    fig.update_layout(height=150, width=270, margin=dict(t=20, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=False, key=f'gauge_{i}_{j}')
                
    else:
        st.warning("선택한 국가와 HS CODE 데이터가 없습니다.")

st.markdown("---")


st.title("⚖️ 화장품 수출 관련 법률 정보")

if 'legal_info_loaded' not in st.session_state:
    st.session_state.legal_info_loaded = False
    st.session_state.legal_info = ""

if st.button("📖 법률 요약하기", key="get_legal_summary", type="primary"):
    summary = get_legal_info(selected_country)
    st.session_state.legal_info = summary
    st.session_state.legal_info_loaded = True
    st.rerun() 

if not st.session_state.legal_info_loaded:
    st.info(f"'{selected_country}' 국가의 화장품 수출 관련 법률 정보를 분석하려면 위의 '법률 요약하기' 버튼을 클릭하세요.")
else:
    result = st.session_state.legal_info
    
    is_error = isinstance(result, str) and result.startswith(("오류:", "서버 오류", "네트워크 오류", "알 수 없는 오류", "요청 시간이 초과", "법률 정보 처리 실패", "선택한 국가의"))
    
    if is_error:
        st.error(result)
        if st.button("🔄 다시 시도", key="retry_legal_info"):
            get_legal_info.clear()
            st.session_state.legal_info_loaded = False
            st.session_state.legal_info = ""
            st.rerun()
    else:
        st.markdown("---")
        st.markdown(result, unsafe_allow_html=True)


st.markdown("#### ℹ️ 법률 정보 이용 안내")
st.markdown("""
**주의사항:**
- 본 법률 정보는 참고용으로만 사용하시기 바랍니다.
- 실제 수출 전에는 반드시 해당 국가의 최신 법률 및 규정을 확인하시기 바랍니다.
- 법률 정보는 변경될 수 있으므로 정기적으로 업데이트를 확인해주세요.

**데이터 출처:**
- 법제처 세계법제정보센터 (world.moleg.go.kr)
- AI 분석을 통한 요약 정보
""")