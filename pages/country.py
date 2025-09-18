import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="국가 상세", layout="wide")

st.title("🌎 국가 상세 페이지")

@st.cache_data
def load_excel(path):
    trade_df = pd.read_excel(path, sheet_name="Trade Indicator")
    kpi_df = pd.read_excel(path, sheet_name="KPI")
    return trade_df, kpi_df

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

country_code_map = {
    "미국": "US", "베트남": "VN", "브라질": "BR", "영국": "GB",
    "인도": "IN", "인도네시아": "ID", "일본": "JP", "중국": "CN",
    "태국": "TH", "튀르키예": "TR", "프랑스": "FR", "UAE": "AE"
}

# img_path = os.path.join("data", "img", f"{country_code_map[selected_country]}.jpg")
img = f"https://www.kotra.or.kr/bigdata/resources/images/nation/{country_code_map[selected_country]}.jpg"
url = f'https://www.kotra.or.kr/bigdata/marketAnalysis#search/{country_code_map[selected_country]}'

# 국기, KPI 카드
col1, col2 = st.columns([1, 3])  
with col1:

    st.markdown(
        f"""
        <a href="{url}" target="_blank">
            <img src="{img}" alt="{selected_country}">
        </a>
        """,
        unsafe_allow_html=True
    )
    
    # if os.path.exists(img_path):
    #     st.image(img_path, caption=selected_country, use_container_width=False)
    
with col2:
    kpi_row = kpi_df[kpi_df["국가"] == selected_country]
    if not kpi_row.empty:
        kpi_cols = [col for col in kpi_df.columns if col != "국가"]
        kpi_units = ["$", "건", "건", "건", "백만$"]

        cols = st.columns(5)

        for col, kpi_name, unit in zip(cols, kpi_cols, kpi_units):
            value = kpi_row.iloc[0][kpi_name]
            # HTML로 value와 unit 나누고 unit만 작게
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
default_index = 0

col1, col2 = st.columns([1.5, 3]) 
with col1:
    selected_hscode = st.selectbox("HS CODE 선택", available_hscodes, index=default_index)
    row = trade_df[(trade_df["국가"] == selected_country) & (trade_df["HSCODE"] == selected_hscode)]
    if not row.empty:
        radar_data = row.melt(id_vars=["국가", "HSCODE"],var_name="지표",value_name="값")
        # fig = px.line_polar(radar_data, r="값", theta="지표", line_close=True)
        fig = px.line_polar(radar_data, r="값", theta="지표", line_close=True, hover_name="지표", hover_data={"값": True})
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
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=r["값"],
                        number={'valueformat': '.1f'},
                        title=None,
                        gauge={
                            'axis': {'range': [0, 10], 'dtick': 11},
                            'bar': {'thickness': 1.0}             
                        }
                    ))
                    fig.update_layout(height=150, width=270, margin=dict(t=20, b=0, l=0, r=0))
                    # fig.add_annotation(
                    #     x=0.5, y=1.3, xref='paper', yref='paper', 
                    #     text=r["지표"], showarrow=False, font=dict(size=16)
                    # )
                    st.plotly_chart(fig, use_container_width=False, key=f'gauge_{i}_{j}')
                
    else:
        st.warning("선택한 국가와 HS CODE 데이터가 없습니다.")