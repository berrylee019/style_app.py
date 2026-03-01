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
model = genai.GenerativeModel('gemini-2.5-flash')
prompt = """
당신은 세계 최고의 패션 스타일리스트이자 퍼스널 쇼퍼입니다. 
업로드된 영상을 분석하여 다음 항목을 포함한 '프리미엄 스타일 리포트'를 작성하세요.

1. 스타일 페르소나: 현재 스타일을 정의하는 멋진 키워드
2. 체형 및 핏 분석: 옷의 실루엣이 체형과 얼마나 잘 어울리는지 분석
3. 컬러 매칭: 착용한 옷의 색상 조화와 추천 퍼스널 컬러
4. 개선 제안: 더 완벽한 룩을 위한 한 가지 포인트 조언

모든 내용은 한국어로, 아주 친절하고 전문적인 톤으로 작성하세요. 
중요한 제목 앞에는 #을 붙여서 구분해 주세요.
"""
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

            # --- 73번 줄: [완성본] PDF 생성 기계 및 다운로드 섹션 ---
            def create_pdf_file(text_content):
                from fpdf import FPDF
                from datetime import datetime
                import re

                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.set_margins(left=20, top=20, right=20)
                pdf.set_auto_page_break(auto=True, margin=25)
                pdf.add_page()
                
                try:
                    pdf.add_font('Nanum', '', 'NanumGothic.ttf')
                    pdf.set_font('Nanum', '', 12)
                except:
                    pdf.set_font("Arial", size=11)

                pdf.set_text_color(50, 50, 50)
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(170, 15, "AI STYLE PREMIUM ANALYSIS REPORT", ln=True, align='C')
                
                pdf.set_font("Arial", size=9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(170, 5, f"Report ID: {datetime.now().strftime('%Y%m%d%H%M%S')}", ln=True, align='C')
                pdf.ln(15)

                pdf.set_text_color(0, 0, 0)
                clean_text = text_content.replace('#', '').strip()
                
                for line in clean_text.split('\n'):
                    line = line.strip()
                    if line:
                        pdf.set_x(20) # 왼쪽 정렬 고정!
                        try:
                            pdf.set_font('Nanum', '', 11)
                            pdf.multi_cell(170, 8, txt=line, align='L')
                        except:
                            pdf.set_font("Arial", size=11)
                            pdf.multi_cell(170, 8, txt=line.encode('ascii', 'ignore').decode('ascii'), align='L')
                    else:
                        pdf.ln(2)

                pdf.ln(10)
                pdf.set_x(20)
                pdf.set_font("Arial", size=8)
                pdf.set_text_color(180, 180, 180)
                pdf.cell(170, 10, "Copyright 2026. Microhard All rights reserved.", align='C')
                
                return pdf.output(dest='S')

            # --- 여기서부터 화면에 버튼을 그리는 코드입니다요! (사라졌던 부분) ---
            # --- 123번 줄: [무료 이벤트 버전] 리포트 섹션 ---
            st.divider()
            st.subheader("🎁 프리미엄 리포트 무료 나눔 이벤트")
            st.write("지금 분석 결과를 PDF 리포트로 소장해 보세요. 오픈채팅으로 문의 주시면 열람 비밀번호를 즉시 알려드립니다!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### **비밀번호 받는 법**")
                st.write("✅ **현재 가격:** ~~9,900원~~ → **0원 (한시적 무료)**")
                # 형님 오픈채팅 링크로 연결해주셔요!
                st.link_button("💬 비밀번호 무료 문의하기", "https://open.kakao.com/o/your_link") 
            
            with col2:
                # 고객이 카톡으로 받아온 비번을 입력하는 곳입니다요
                input_pw = st.text_input("전송받은 비밀번호를 입력하세요.", type="password", key="free_event_pw")

            # 비밀번호 검증 (여전히 style77로 작동합니다요!)
            if input_pw == "style77":
                try:
                    pdf_data = create_pdf_file(st.session_state.analysis_result)
                    st.success("✅ 인증되었습니다! 아래 버튼을 눌러 리포트를 다운로드하세요.")
                    st.download_button(
                        label="📄 프리미엄 PDF 리포트 다운로드",
                        data=bytes(pdf_data),
                        file_name="Style_Premium_Report.pdf",
                        mime="application/pdf",
                        key="event_dl_button"
                    )
                except Exception as e:
                    st.error(f"리포트 생성 중 오류 발생: {e}")
            elif input_pw != "":
                st.warning("⚠️ 비밀번호가 틀렸습니다. 오픈채팅으로 문의해 주세요!")
