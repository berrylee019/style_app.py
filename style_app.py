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
        # 1. 화면에 업로드된 영상 보여주기
        st.video(uploaded_file)
        
        # 2. 분석 결과 기억력 주머니(Session State) 설정
        # (비밀번호 입력 시 분석 결과가 사라지는 것을 방지합니다요!)
        if 'analysis_result' not in st.session_state:
            if st.button("✨ AI 스타일 분석 시작"):
                with st.status("🔍 AI가 영상을 정밀 분석 중입니다...", expanded=True) as status:
                    bytes_data = uploaded_file.getvalue()
                    image_parts = [{"mime_type": uploaded_file.type, "data": bytes_data}]
                    
                    # AI에게 분석 요청 (형님의 프롬프트와 영상을 보냅니다)
                    try:
                        response = model.generate_content([prompt, image_parts[0]])
                        st.session_state.analysis_result = response.text
                        status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                    except Exception as e:
                        st.error(f"분석 중 오류가 났구먼유: {e}")

        # 3. 분석 결과가 주머니에 있다면 화면에 출력
        if 'analysis_result' in st.session_state:
            st.subheader("📊 AI 스타일 리포트")
            st.markdown(st.session_state.analysis_result)
            st.balloons()

            # --- 4. PDF 생성 기계 (고급형) ---
            def create_pdf_file(text_content):
                from fpdf import FPDF
                from datetime import datetime
                pdf = FPDF()
                pdf.add_page()
                try:
                    pdf.add_font('Nanum', '', 'NanumGothic.ttf')
                    pdf.set_font('Nanum', '', 12)
                except:
                    pdf.set_font("Arial", size=11)

                pdf.set_text_color(40, 40, 40)
                pdf.cell(0, 10, "MICROHARD AI STYLE PREMIUM REPORT", ln=True, align='C')
                pdf.set_font("Arial", size=8)
                pdf.cell(0, 5, f"Issued Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
                pdf.ln(10)

                clean_text = text_content.encode('utf-8', 'ignore').decode('utf-8')
                for line in clean_text.split('\n'):
                    if line.strip():
                        pdf.multi_cell(0, 8, txt=line)
                return pdf.output(dest='S')

            # --- 5. 수익화 섹션 (비밀번호 로직) ---
            st.divider()
            st.subheader("💎 프리미엄 PDF 리포트 소장하기")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("✅ **리포트 가격: 9,900원**")
                # 형님 오픈채팅 링크로 바꾸셔요!
                st.link_button("💰 입금 및 비번 문의", "https://open.kakao.com/o/your_link") 
            
            with col2:
                input_pw = st.text_input("열람 비밀번호 입력", type="password", key="premium_pw")

            # 비밀번호 검증 및 다운로드 버튼
            if input_pw == "style77":
                try:
                    pdf_data = create_pdf_file(st.session_state.analysis_result)
                    st.success("🔓 인증 성공! 아래 버튼을 눌러주십쇼 형님!")
                    st.download_button(
                        label="📄 프리미엄 PDF 리포트 다운로드",
                        data=bytes(pdf_data),
                        file_name="Style_Premium_Report.pdf",
                        mime="application/pdf",
                        key="dl_button_final"
                    )
                except Exception as e:
                    st.error(f"리포트 생성 중 오류 발생: {e}")
            elif input_pw != "":
                st.warning("❌ 비밀번호가 틀렸습니다요!")
