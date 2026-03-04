import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import os

# 1. API 키 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다요! .streamlit/secrets.toml을 확인해 주셔요.")

# 페이지 설정
st.set_page_config(page_title="AI 스타일 가이드", page_icon="👗", layout="centered")

# --- [디자인 그대로!] 커스텀 CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.1rem; color: #64748B; text-align: center; margin-bottom: 2rem; }
    
    .tip-card { 
        background-color: #f8fafc; border-radius: 10px; padding: 20px; 
        border-left: 5px solid #3B82F6; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        height: 100%; margin-bottom: 10px;
    }
    .tip-header { font-weight: 700; color: #1E40AF; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
    
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3rem; 
        background-color: #2563EB; color: white; font-weight: 700; border: none; transition: all 0.3s; 
    }
    .stButton>button:hover { background-color: #1E40AF; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

# --- PDF 생성 함수 ---
def create_pdf_file(text_content):
    pdf = FPDF()
    pdf.add_page()
    font_path = "NanumGothic.ttf"
    
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else:
        pdf.set_font("Arial", size=12)
        text_content = "Font file missing. Check NanumGothic.ttf"

    pdf.set_text_color(31, 41, 55)
    pdf.cell(200, 10, txt="AI PREMIUM STYLE REPORT", ln=True, align='C')
    pdf.ln(10)
    
    clean_text = text_content.replace('#', '').strip()
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output()

# --- 헤더 섹션 (Styley 인사말) ---
col_img, col_txt = st.columns([1, 4])
with col_img:
    if os.path.exists("styley.png"):
        st.image("styley.png", width=110)
    else:
        st.write("🖼️")

with col_txt:
    st.markdown("""
        <div style="position: relative; background: #E1F5FE; border-radius: 15px; padding: 15px; margin-top: 10px; border: 1px solid #B3E5FC;">
            <strong style="color: #0288D1; font-size: 1.1rem;">Styley:</strong><br>
            <span style="color: #333;">"반가워요 형님! 가이드 영상을 참고해서 360도 촬영본을 올려주셔요. <br>오늘의 베스트 룩을 찾아드릴게유! ✨"</span>
            <div style="position: absolute; left: -10px; top: 20px; width: 0; height: 0; border-top: 10px solid transparent; border-bottom: 10px solid transparent; border-right: 10px solid #E1F5FE;"></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">👗 AI 스타일 가이드</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</p>', unsafe_allow_html=True)

# --- 촬영 가이드 및 업로드 섹션 ---
st.markdown("#### 📹 촬영 가이드 및 업로드")
c_v, c_u = st.columns([1.2, 1])

with c_v:
    if os.path.exists("sample_guide.mp4"):
        st.video("sample_guide.mp4")
    else:
        st.info("가이드 영상(sample_guide.mp4)을 준비해 주셔요!")

with c_u:
    uploaded_file = st.file_uploader("영상을 업로드하세요", type=["mp4", "mov", "avi"])
    if uploaded_file:
        st.success("영상 준비 완료! 아래 분석 버튼을 눌러주셔요.")

# --- 꿀팁 섹션 (카드형) ---
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="tip-card"><div class="tip-header">👤 1. 전신 샷 필수</div>머리부터 발끝까지 화면에 다 들어와야 해요.</div><br><div class="tip-card"><div class="tip-header">🔄 2. 360도 회전</div>천천히 한 바퀴 돌아주시면 입체적 분석이 가능합니다.</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="tip-card"><div class="tip-header">💡 3. 밝은 조명</div>조명이 밝아야 컬러를 정확히 잡아내요.</div><br><div class="tip-card"><div class="tip-header">⏱️ 4. 5~15초 권장</div>너무 길면 업로드가 느려질 수 있어요.</div>', unsafe_allow_html=True)

# --- 분석 실행 ---
if uploaded_file is not None:
    st.divider()
    if 'analysis_result' not in st.session_state:
        if st.button("✨ AI 스타일 분석 시작"):
            with st.status("🔍 AI가 스타일을 정밀 분석 중입니다...", expanded=True) as status:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    video_part = {"mime_type": uploaded_file.type, "data": uploaded_file.read()}
                    prompt = "패션 전문가로서 영상 속 인물의 #패션 점수, #체형 분석, #개선 제안을 한국어로 상세히 리포트해 주세요."
                    response = model.generate_content([prompt, video_part])
                    st.session_state.analysis_result = response.text
                    status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"분석 오류: {e}")

    # --- 결과 출력 및 수익화 섹션 ---
    if 'analysis_result' in st.session_state:
        st.success("분석이 완료되었습니다!")
        st.subheader("📊 AI 프리미엄 스타일 리포트")
        st.markdown(st.session_state.analysis_result)
        st.balloons()

        st.divider()
        st.markdown("### 🚀 스타일 업그레이드 본부")
        res_c1, res_c2 = st.columns([1.2, 1])
        
        with res_c1:
            st.info("💡 **카페 회원 혜택**\n- 리포트 PDF 저장 가능\n- 코디 가이드북 즉시 증정")
            st.link_button("☕ 카페에서 비번 확인하기", "https://cafe.naver.com/stylely")
        
        with res_c2:
            input_pw = st.text_input("카페 비밀번호를 입력하세요", type="password")
            if input_pw == "style77":
                try:
                    pdf_data = create_pdf_file(st.session_state.analysis_result)
                    st.download_button(
                        label="📄 PDF 리포트 다운로드",
                        data=bytes(pdf_data),
                        file_name=f"Style_Report_{datetime.now().strftime('%m%d')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"PDF 생성 중 글꼴 에러가 났구먼유: {e}")

st.markdown("<br><br><p style='text-align: center; color: #94a3b8; font-size: 0.8rem;'>Copyright 2026. Microhard All rights reserved.</p>", unsafe_allow_html=True)

