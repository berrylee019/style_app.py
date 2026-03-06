import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import streamlit.components.v1 as components

# --- [기능] 불꽃놀이 시스템 ---
def trigger_fireworks():
    st.session_state.do_fireworks = True

def display_fireworks():
    if st.session_state.get('do_fireworks', False):
        fireworks_js = """
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                zIndex: 9999
            });
        </script>
        """
        components.html(fireworks_js, height=0)
        st.session_state.do_fireworks = False

# --- [설정] API 키 및 페이지 ---
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다요! secrets.toml 확인 부탁드려유.")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [디자인] 럭셔리 흑백 테마 CSS ---
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #111827; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3rem; background-color: #111827; color: white; }
    .stInfo { border-radius: 15px; border-left: 10px solid #111827; }
    </style>
    """, unsafe_allow_html=True)

# --- [기능] PDF 생성 엔진 ---
def create_recipe_pdf(content):
    def clean_text(text):
        return re.sub(r'\*\*|\*|__|#', '', text).strip()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else: pdf.set_font("Arial", size=12)

    pdf.set_fill_color(17, 24, 39) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.text(15, 25, "AI BLACK & WHITE CHEF REPORT")
    
    pdf.set_y(50)
    pdf.set_text_color(31, 41, 55)
    pdf.multi_cell(0, 8, txt=clean_text(content))
    return pdf.output()

# --- [UI] 메인 화면 ---
st.markdown('<p class="main-title">👨‍🍳 Microhard AI 흑백요리사</p>', unsafe_allow_html=True)

st.info("""
    **💡 이용 방법:**
    1. 냉장고 안의 재료 사진을 올려주셔요.
    2. AI가 **백수저(영양)** vs **흑수저(맛/속도)** 대결 레시피를 제안합니다.
    3. 형님의 체형에 딱 맞는 최적의 식단을 확인해 보셔요!
""")

with st.expander("❓ 서비스 특징"):
    st.write("- 식재료 최적 활용 가이드")
    st.write("- 맞춤형 탄/단/지 비율 분석")
    st.write("- 셰프의 킥이 담긴 서바이벌 레시피")

# --- [기능] 사진 업로드 및 분석 ---
uploaded_img = st.file_uploader("냉장고 재료 사진을 올려주셔요", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, caption="분석할 재료", use_container_width=True)
    
    if st.button("🍴 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 검토 중입니다...", expanded=True) as status:
            try:
                # 1. 모델명 수정 (gemini-1.5-flash가 현재 표준입니다요)
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
                prompt = """당신은 AI 흑백요리사 영양사입니다. 다음 순서로 리포트하세요(마크다운 기호 금지):
                1. 식별된 재료 리스트
                2. [백수저 모드] - 영양 완벽형 (조리법, 칼로리, 탄단지 비율)
                3. [흑수저 모드] - 맛과 속도 중심 (빠른 조리법, 셰프의 킥)"""
                
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                
                status.update(label="✅ 분석 완료! 결투 결과가 나왔습니다!", state="complete", expanded=False)
                
                # 2. 분석 완료 후 불꽃놀이 예약 및 리런
                trigger_fireworks()
                st.rerun()

            except Exception as e:
                st.error(f"오류 발생: {e}")

# --- [UI] 분석 결과 전시 ---
if 'chef_result' in st.session_state:
    st.divider()
    st.subheader("🏁 셰프들의 제안")
    st.write(st.session_state.chef_result)

    input_pw = st.text_input("리포트 잠금해제 (style77)", type="password")
    if input_pw == "style77":
        # 비밀번호 인증 시 불꽃놀이 한 번 더! (처음 한 번만 실행되도록 체크)
        if not st.session_state.get('pdf_unlocked', False):
            st.session_state.pdf_unlocked = True
            trigger_fireworks()
            st.rerun()
            
        pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
        st.download_button(
            label="📄 흑백요리사 식단 리포트 다운로드",
            data=bytes(pdf_bytes),
            file_name="Chef_Report.pdf",
            mime="application/pdf"
        )

# --- [마무리] 불꽃놀이 실행 (항상 맨 아래 대기) ---
display_fireworks()
