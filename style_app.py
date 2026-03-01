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
        status_text = st.empty() # 진행 상황을 보여줄 빈 칸 마련
        
        with st.spinner("AI가 영상을 시청하며 스타일을 분석 중입니다..."):
            # 1단계: 파일 저장 확인
            status_text.info("1단계: 서버에 임시 파일 생성 중...")
            # 임시 파일 저장 (Gemini API는 경로를 필요로 함)
            with open("temp_video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())
            # 2단계: 구글 AI 서버로 전송
            status_text.info("2단계: 구글 AI 엔진으로 영상 전송 중...")
            # 3. 비디오 업로드 및 처리 대기
            video_file = genai.upload_file(path="temp_video.mp4")

            # 3단계: AI의 영상 처리 대기 (여기가 가장 오래 걸립니다)
        
            # 상태 확인 루프 보강
        start_time = time.time()
        # with st.spinner("AI가 영상을 시청하기 위해 준비 중입니다..."):
        while video_file.state.name == "PROCESSING":
            elapsed = int(time.time() - start_time)
            status_text.warning(f"3단계: AI가 영상을 시청하며 분석 중... ({elapsed}초 경과)")
            time.sleep(3)
            video_file = genai.get_file(video_file.name)
            
            # 너무 오래 걸리면(예: 3분) 강제 종료
            if elapsed > 180:
                st.error("시간 초과! 영상이 너무 크거나 구글 서버가 바쁩니다.")
                st.stop()
                
        if video_file.state.name == "FAILED":
            st.error("비디오 처리 중 오류가 발생했습니다.")
            st.stop()

            # 4단계: 최종 리포트 생성
            # 4. 분석 수행
            status_text.success("4단계: 분석 완료! 리포트를 작성합니다...")
            model = genai.GenerativeModel("gemini-1.5-flash") # 또는 2.0-flash

            # 안전 장치: 프롬프트를 더 명확하게
            prompt = "너는 세계적인 패션 스타일리스트야. 이 영상 속 인물의 스타일을 분석하고, 1. 전반적인 룩의 특징 2. 어울리는 액세서리 추천 3. 개선할 점을 전문적으로 알려줘."
            response = model.generate_content([
                video_file, prompt])
            
            st.subheader("📊 AI 스타일 리포트")
            if response.text:
            st.write(response.text)
            status_text.empty() # 진행 상황 메시지 삭제
        else:
            st.write("분석 결과가 비어 있습니다. 다른 영상으로 시도해 보세요.")


