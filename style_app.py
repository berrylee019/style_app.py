import streamlit as st
import google.generativeai as genai
import time

# 1. API 키 설정 (이미 Secrets에 등록된 MY_API_KEY 사용)
genai.configure(api_key=st.secrets["MY_API_KEY"])

st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗")
st.title("👗 AI 스타일 가이드: 실시간 비디오 분석")

# 2. 비디오 업로드 섹션
uploaded_file = st.file_uploader("분석할 쇼핑/스타일 영상을 업로드하세요.", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    st.video(uploaded_file)
    
    if st.button("🚀 스타일 분석 시작"):
        with st.spinner("AI가 영상을 시청하며 스타일을 분석 중입니다..."):
            # 임시 파일 저장 (Gemini API는 경로를 필요로 함)
            with open("temp_video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 3. 비디오 업로드 및 처리 대기
            video_file = genai.upload_file(path="temp_video.mp4")

            # 상태 확인 루프 보강
        with st.spinner("AI가 영상을 시청하기 위해 준비 중입니다..."):
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
        if video_file.state.name == "FAILED":
            st.error("비디오 처리 중 오류가 발생했습니다.")
            st.stop()
            
            # 4. 분석 수행
            model = genai.GenerativeModel("gemini-1.5-flash") # 또는 2.0-flash
            response = model.generate_content([
                video_file,
                "너는 세계적인 패션 스타일리스트야. 이 영상 속 인물의 스타일을 분석하고, "
                "1. 전반적인 룩의 특징 2. 어울리는 액세서리 추천 3. 개선할 점을 전문적으로 알려줘."
            ])
            
            st.subheader("📊 AI 스타일 리포트")

            st.write(response.text)
