import streamlit as st
import requests
import json

# n8n에서 복사한 Webhook URL
n8n_webhook_url = "https://hahah.app.n8n.cloud/webhook/legal-info-webhook"

st.title("국가별 법률 정보 요약")

# 사용자에게 국가 이름을 입력받습니다.
country_name = st.text_input("국가 이름을 입력하세요 (예: 중국, 일본, 미국)")

# n8n 트리거 시작
if st.button("요약 시작"):
    if country_name:
        with st.spinner("처리 중... (최대 10분 소요될 수 있습니다)"):
            payload = {"country": country_name}

            try:
                # 타임아웃을 600초(10분)로 설정
                response = requests.post(
                    n8n_webhook_url, 
                    params=payload, 
                    timeout=600
                )
                
                response.raise_for_status()  # 200번대 코드가 아니면 에러 발생

                # JSON 응답 파싱
                try:
                    result = response.json()
                    
                    # 배열인지 확인하고 첫 번째 요소 가져오기
                    if isinstance(result, list) and len(result) > 0:
                        result = result[0]
                    
                        
                        # 요약 내용 표시
                        if result.get('summary'):
                            st.write(result.get('summary'))
                            
                    else:
                        # n8n에서 오류가 발생한 경우
                        st.error("처리 중 오류가 발생했습니다")
                        st.write(f"오류 메시지: {result.get('error', '알 수 없는 오류')}")
                        
                except json.JSONDecodeError:
                    # JSON이 아닌 응답이 온 경우
                    st.warning("예상과 다른 응답 형식입니다")
                    st.text("응답 내용:")
                    st.code(response.text)
                
            except requests.exceptions.Timeout:
                st.error("⏰ 처리 시간이 너무 오래 걸렸습니다")
                st.info("파일이 크거나 네트워크가 느릴 수 있습니다. 잠시 후 다시 시도해주세요.")
                
            except requests.exceptions.RequestException as e:
                st.error(f"🚨 연결 오류가 발생했습니다")
                st.write(f"오류 상세: {e}")
                st.info("n8n 워크플로우가 실행 중인지 확인해주세요.")
            
    else:
        st.warning("⚠️ 국가 이름을 입력해주세요.")