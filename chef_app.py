import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import streamlit.components.v1 as components

# --- [1. 불꽃놀이 시스템: 무한루프 방지형] ---
def trigger_fireworks():
    st.session_state.do_fireworks = True

def display_fireworks():
    # 실행 후 즉시 상태를 초기화해서 루프를 끊어버립니다요!
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
        st.session_state.do_fireworks = False # 여기서 바로 꺼주는 게 핵심!

# --- [2. 설정 및 세션 초기화] ---
if 'do_fireworks' not in st.session_state:
    st.session_state.do_fireworks = False
if 'pdf_unlocked' not in st.session_state:
    st.session_state.pdf_unlocked = False

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다요!")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [3. 디자인 CSS] ---
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #111827; text-align: center; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #111827; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- [4. PDF 생성 함수] ---
def create_recipe_pdf(content):
    def clean_text(text):
        return re.sub(r'\*\*|\*|__|#', '', text).strip()
    pdf = FPDF()
    pdf.add_page()
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else: pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=clean_text(content))
    return pdf.output()

# --- [5. UI 메인 화면] ---
st.markdown('<p class="main-title">👨‍🍳 Microhard AI 흑백요리사</p>', unsafe_allow_html=True)

uploaded_img = st.file_uploader("냉장고 재료 사진을 올려주셔요", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, caption="분석할 재료", use_container_width=True)
    
    if st.button("🍴 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 분석 중...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
                prompt = "식재료 리스트와 백수저(영양), 흑수저(맛) 레시피를 마크다운 없이 작성해줘."
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                
                # 🔥 루프 방지: 상태 변경 후 한 번만 트리거!
                trigger_fireworks()
                st.rerun()

            except Exception as e:
                st.error(f"오류 발생: {e}")

# --- [6. 결과 전시 및 다운로드] ---
if 'chef_result' in st.session_state:
    st.divider()
    st.subheader("🏁 셰프들의 제안")
    st.write(st.session_state.chef_result)

    input_pw = st.text_input("리포트 잠금해제 (style77)", type="password")
    if input_pw == "style77":
        # 비밀번호 인증 시 딱 한 번만 불꽃놀이!
        if not st.session_state.pdf_unlocked:
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

# --- [7. 마무리: 불꽃놀이 실행기] ---
display_fireworks()
