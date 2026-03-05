import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import os
import re

# 1. API 키 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다요! secrets.toml을 확인해 주셔요.")

# 페이지 설정
st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗", layout="centered")

# --- [디자인] 커스텀 CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 0.5rem; }
    .tip-card { background-color: #f8fafc; border-radius: 10px; padding: 15px; border-left: 5px solid #3B82F6; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- [기능] 프리미엄 PDF 생성 함수 (2.0 버전) ---
def create_pdf_file(text_content):
    def clean_text(text):
        text = text.replace('**', '').replace('__', '')
        text = text.replace('* ', ' • ')
        text = re.sub(r'\.{2,}', '.', text)
        return text.strip()

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    epw = pdf.w - 20 

    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else:
        pdf.set_font("Arial", size=12)

    # 헤더 디자인
    pdf.set_fill_color(28, 35, 49) 
    pdf.rect(0, 0, 210, 45, 'F')
    if os.path.exists("styley.png"):
        pdf.image("styley.png", 15, 12, 22)
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(45, 18)
    pdf.set_font('Nanum', '', 22)
    pdf.cell(0, 10, "PREMIUM STYLE ANALYSIS", ln=True)
    pdf.set_font('Nanum', '', 10)
    pdf.set_xy(45, 28)
    pdf.cell(0, 10, f"Microhard AI Lab | {datetime.now().strftime('%Y.%m.%d')}", ln=True)

    # 본문
    pdf.set_y(55)
    lines = text_content.split('\n')
    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            pdf.ln(4)
            continue
        if raw_line.startswith('#'):
            pdf.ln(5)
            pdf.set_font('Nanum', '', 15)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(epw, 10, clean_text(raw_line.replace('#', '')), ln=True)
            pdf.line(10, pdf.get_y(), 50, pdf.get_y())
            pdf.ln(3)
        else:
            pdf.set_font('Nanum', '', 11)
            pdf.set_text_color(44, 62, 80)
            pdf.multi_cell(epw, 7, txt=clean_text(raw_line))
    
    return pdf.output()

# --- [UI] 헤더 ---
st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)

# --- [기능] 영상 업로드 ---
uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.divider()
    if 'analysis_result' not in st.session_state:
        if st.button("✨ 프리미엄 스타일 분석 시작"):
            with st.status("🔍 전문 컨설턴트 AI가 수치 분석 중...", expanded=True) as status:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                    
                    # --- 형님이 요청하신 수치화 프롬프트 반영! ---
                    prompt = """
                    당신은 수치 데이터에 기반한 최고급 패션 컨설턴트입니다. 
                    영상을 분석하여 반드시 다음 항목들을 포함해 리포트해 주세요:
                    
                    # 1. 신체 비율 및 대칭성 분석
                    - 상체와 하체의 비율을 수치(예: 4.2:5.8)로 제시하고 분석하세요.
                    - 어깨 선의 대칭성 점수(100점 만점)와 불균형 여부를 진단하세요.
                    
                    # 2. 색상 보완성(Complementary Color) 리포트
                    - 현재 착용한 의상의 색상 조합 점수를 산출하세요.
                    - 사용자의 피부톤과 대조되는 '보완색'을 추천하고 그 이유를 설명하세요.
                    
                    # 3. 종합 스타일링 제언
                    - 위 수치를 바탕으로 가장 개선이 필요한 부분 1가지를 제언하세요.
                    
                    ** 이나 * 같은 마크다운 기호는 절대 사용하지 말고 깔끔한 문장으로 작성해 주세요.
                    """
                    
                    response = model.generate_content([prompt, video_part])
                    st.session_state.analysis_result = response.text
                    status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"분석 오류: {e}")

    # --- 결과 및 다운로드 ---
    if 'analysis_result' in st.session_state:
        st.subheader("📊 AI 프리미엄 수치 분석 리포트")
        st.markdown(st.session_state.analysis_result)

        st.divider()
        input_pw = st.text_input("카페 비밀번호 입력 (style77)", type="password")
        if input_pw == "style77":
            pdf_data = create_pdf_file(st.session_state.analysis_result)
            st.download_button(
                label="📄 전문 PDF 리포트 다운로드",
                data=bytes(pdf_data),
                file_name=f"Premium_Report_{datetime.now().strftime('%m%d')}.pdf",
                mime="application/pdf"
            )
