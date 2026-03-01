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

            # 3단계: AI의 영상 처리 대기 (새로고침 강화 버전)
        start_time = time.time()
        while True:
            video_file = genai.get_file(video_file.name) # 구글 서버에서 상태 다시 가져오기
            elapsed = int(time.time() - start_time)
            
            if video_file.state.name == "ACTIVE":
                status_text.success(f"3단계 완료! (총 {elapsed}초 소요)")
                break
            elif video_file.state.name == "FAILED":
                st.error("AI가 영상 분석에 실패했습니다. 파일 형식을 확인해주세요.")
                st.stop()
            
            # 진행 중임을 알리는 애니메이션 효과
            dots = "." * (elapsed % 4)
            status_text.warning(f"3단계: AI가 영상을 시청하는 중입니다{dots} ({elapsed}초 경과)")
            
            time.sleep(2) # 2초마다 확인

            if elapsed > 120: # 2분 넘어가면 비상 정지
                st.error("영상 처리가 너무 오래 걸립니다. 다시 시도해 주세요.")
                st.stop()

            # 4단계: 최종 리포트 생성 (가시성 강화)
            status_text.info("4단계: 스타일리스트가 영상을 다 봤습니다! 이제 리포트를 작성합니다... 📝")
        
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = "너는 세계적인 패션 스타일리스트야. 영상 속 인물의 스타일을 분석하고, 1. 전반적인 룩의 특징 2. 어울리는 액세서리 추천 3. 개선할 점을 전문적으로 알려줘."

            try:
                # AI에게 답변 요청
                response = model.generate_content([video_file, prompt])
            
                # 결과 출력
                st.subheader("📊 AI 스타일 리포트")
                if response.text:
                    # 기존의 st.write나 st.markdown 줄을 아래 내용으로 교체
                    st.balloons() # 분석 성공 축하 풍선! 🎈
                    st.success("✅ Microhard AI 스타일리스트가 분석을 마쳤습니다!")
                    st.markdown(response.text) # 리포트 본문 출력
                    status_text.success("✅ 모든 분석이 완료되었습니다!")
                else:
                    st.write("AI가 답변을 생성하지 못했습니다. (안전 필터 작동 가능성)")
                
            except Exception as e:
                st.error(f"리포트 생성 중 오류 발생: {e}")
                # 만약 여기서 막힌다면 Streamlit 로그(Manage app -> Logs)를 확인해야 합니다.







