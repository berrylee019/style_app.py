import streamlit as st
import google.generativeai as genai
import time

# 1. API 키 설정 (이미 Secrets에 등록된 MY_API_KEY 사용)
genai.configure(api_key=st.secrets["MY_API_KEY"])

st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗")
st.title("👗 AI 스타일 가이드: 실시간 비디오 분석")

# 2. 비디오 업로드 섹션
# --- 영상 업로드 가이드 섹션 ---
st.title("✨ AI 퍼스널 스타일 가이드")
st.markdown("### 🤳 당신의 스타일을 10초 만에 분석해 드립니다")

with st.expander("🎥 **더 정확한 분석을 위한 영상 촬영 꿀팁 (필독!)**", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **1. 전신 샷은 필수!** :머리부터 발끝까지 화면에 다 들어와야 정확한 비율 분석이 가능해요.
        
        **2. 천천히 360도 회전** :앞, 옆, 뒤태를 모두 보여주시면 입체적인 핏 가이드를 드립니다.
        """)
    with col2:
        st.markdown("""
        **3. 밝은 곳에서 촬영** :조명이 밝아야 옷의 질감과 퍼스널 컬러를 정확히 잡아내요.
        
        **4. 5~15초 내외 권장** :너무 길면 업로드 시간이 오래 걸려요!
        """)

# 실제 업로드 버튼
uploaded_file = st.file_uploader("분석할 쇼핑/스타일 영상을 업로드하세요.", type=["mp4", "mov", "avi"])

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

            # --- 이미지 처리 및 AI 분석 (60번 줄 이하 통합) ---
            if uploaded_file is not None:
                # 1. 이미지 변환
                bytes_data = uploaded_file.getvalue()
                image_parts = [{"mime_type": uploaded_file.type, "data": bytes_data}]
    
                # 2. AI 분석 요청
                result = model.generate_content([prompt, image_parts[0]])
                
                if result.text:
                    st.subheader("📊 AI 스타일 리포트")
                    st.markdown(result.text)
                    st.balloons()
    
                    # --- PDF 생성 함수 (불필요한 encode 제거) ---
                    # --- [프리미엄 버전] PDF 생성 함수 ---
                def create_pdf_file(text_content):
                    from fpdf import FPDF
                    from datetime import datetime

                    pdf = FPDF()
                    pdf.add_page()
                    
                    # 1. 폰트 설정 (나눔고딕 파일이 있어야 한글이 나옵니다요!)
                    try:
                        pdf.add_font('Nanum', '', 'NanumGothic.ttf')
                        pdf.set_font('Nanum', '', 12)
                    except:
                        pdf.set_font("Arial", size=11)

                    # 2. 헤더: 프리미엄 타이틀 (비싸 보이게!)
                    pdf.set_text_color(40, 40, 40) # 짙은 회색
                    pdf.cell(0, 10, "MICROHARD AI STYLE PREMIUM REPORT", ln=True, align='C')
                    
                    # 발행 일자 넣기
                    pdf.set_font("Arial", size=8)
                    pdf.cell(0, 5, f"Issued Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
                    pdf.ln(10) # 한 줄 띄우기

                    # 3. 본문: AI 답변 정리해서 넣기
                    pdf.set_font('Nanum', '', 11) if 'Nanum' in pdf.fonts else pdf.set_font("Arial", size=11)
                    
                    # 특수문자 에러 방지 및 줄바꿈 처리
                    clean_text = text_content.encode('utf-8', 'ignore').decode('utf-8')
                    for line in clean_text.split('\n'):
                        if line.strip():
                            # 제목(#으로 시작하는 줄)은 조금 더 크게!
                            if line.startswith('#'):
                                pdf.set_font('Nanum', '', 13) if 'Nanum' in pdf.fonts else pdf.set_font("Arial", size=13)
                                pdf.multi_cell(0, 10, txt=line.replace('#', '').strip())
                                pdf.set_font('Nanum', '', 11) if 'Nanum' in pdf.fonts else pdf.set_font("Arial", size=11)
                            else:
                                pdf.multi_cell(0, 8, txt=line)
                    
                    # 4. 푸터: 저작권 표시 (전문가 느낌 물씬!)
                    pdf.ln(20)
                    pdf.set_font("Arial", size=9)
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(0, 10, "© 2026 Microhard Style Solution. All Rights Reserved.", align='C')
                    
                    return pdf.output(dest='S')
    
                    st.divider()
                    st.info("💎 프리미엄 PDF 리포트를 소장하세요.")
    
                    # 3. PDF 데이터 생성 및 버튼 배치
                    try:
                        pdf_data = create_pdf_file(result.text)
                        st.download_button(
                            label="📄 프리미엄 PDF 리포트 다운로드",
                            data=bytes(pdf_data), # 안전하게 바이트로 형변환
                            file_name="Style_Report.pdf",
                            mime="application/pdf",
                            key="final_pdf_button_v3"
                        )
                    except Exception as e:
                        st.error(f"PDF 파일 준비 중 오류가 발생했습니다: {e}")



