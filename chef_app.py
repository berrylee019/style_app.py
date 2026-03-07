import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import streamlit.components.v1 as components

# --- [1. 불꽃놀이 & 축하 시스템] ---
def play_celebration():
    # 1. 스트림릿 내장 풍선 (무조건 실행됨)
    st.balloons()
    
    # 2. 커스텀 폭죽 자바스크립트 (Canvas-Confetti)
    confetti_js = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        var end = Date.now() + 3000;
        var colors = ['#ffffff', '#000000', '#ffd700'];
        (function frame() {
            confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 }, colors: colors });
            confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 }, colors: colors });
            if (Date.now() < end) { requestAnimationFrame(frame); }
        }());
    </script>
    """
    components.html(confetti_js, height=0)

# --- [2. 설정 및 세션 상태 초기화] ---
if 'chef_result' not in st.session_state:
    st.session_state.chef_result = None
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = False

# API 키 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ API 키 설정이 필요합니다요! Secrets 설정을 확인해 주셔요.")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [3. 디자인 및 스타일 CSS] ---
st.markdown("""
    <style>
    .main-title { font-size: 2.8rem; font-weight: 800; color: #111827; text-align: center; margin-bottom: 5px; }
    .sub-title { font-size: 1.1rem; color: #6B7280; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background-color: #111827; color: white; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 12px; background-color: #059669; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- [4. PDF 생성 함수] ---
def create_recipe_pdf(content):
    def clean_text(text):
        return re.sub(r'\*\*|\*|__|#', '', text).strip()
    
    pdf = FPDF()
    pdf.add_page()
    
    # 폰트 설정 (없으면 기본 폰트)
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else:
        pdf.set_font("Arial", size=12)
        
    pdf.set_fill_color(17, 24, 39)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.font_family, size=20)
    pdf.text(15, 25, "AI BLACK & WHITE CHEF REPORT")
    
    pdf.set_y(50)
    pdf.set_text_color(31, 41, 55)
    pdf.set_font(pdf.font_family, size=11)
    pdf.multi_cell(0, 8, txt=clean_text(content))
    return pdf.output()

# --- [5. 메인 UI 화면] ---
st.markdown('<p class="main-title">👨‍🍳 Microhard AI 흑백요리사</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">형님의 냉장고가 최고의 파인 다이닝으로 변신합니다요!</p>', unsafe_allow_html=True)

st.info("💡 **이용 가이드**: 냉장고 재료 사진을 올리고 '대결 시작'을 누르셔요. 셰프들이 형님만을 위한 영양 식단을 설계합니다요.")

uploaded_img = st.file_uploader("📸 냉장고 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, caption="분석 대기 중인 재료", use_container_width=True)
    
    if st.button("🔥 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 엄선하고 있습니다요...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
                prompt = """당신은 사진 속 식재료를 식별하는 AI 흑백요리사입니다. 다음 순서로 리포트하세요:
                1. 식별된 모든 재료 리스트
                2. [백수저 모드] - 영양 완벽형 레시피 (칼로리, 탄단지 포함)
                3. [흑수저 모드] - 맛과 속도 중심 레시피 (셰프의 킥 포함)
                전체 내용을 정중하면서도 전문적인 톤으로 작성하세요 (특수 기호 사용 자제)."""
                
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                status.update(label="✅ 분석이 완료되었습니다요!", state="complete", expanded=False)
                
                # 분석 직후 화끈하게 축하!
                play_celebration()
                
            except Exception as e:
                st.error(f"오류가 났구먼유: {e}")

# --- [6. 결과 출력 및 다운로드 영역] ---
if st.session_state.chef_result:
    st.divider()
    st.subheader("🏁 AI 셰프들의 요리 제안")
    st.write(st.session_state.chef_result)
    
    st.divider()
    st.write("🔓 **프리미엄 리포트 잠금 해제**")
    input_pw = st.text_input("비밀번호를 입력하셔요 (style77)", type="password")
    
    if input_pw == "style77":
        if not st.session_state.unlocked:
            play_celebration() # 비밀번호 맞으면 또 한 번 팡팡!
            st.session_state.unlocked = True
            
        pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
        st.download_button(
            label="📄 흑백요리사 식단 리포트 다운로드 (PDF)",
            data=bytes(pdf_bytes),
            file_name=f"Chef_Report_{uploaded_img.name}.pdf",
            mime="application/pdf"
        )
