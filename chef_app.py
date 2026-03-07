import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import streamlit.components.v1 as components

# --- [1. 축하 시스템: 풍선 + 확실한 폭죽] ---
def play_celebration():
    # 1. 풍선 (안전장치)
    st.balloons()
    
    # 2. 폭죽 (Canvas-Confetti 필살기)
    # iframe 높이를 0이 아닌 1로 살짝 주어 브라우저가 무시하지 못하게 합니다요.
    confetti_js = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        var count = 200;
        var defaults = { origin: { y: 0.7 }, zIndex: 10000 };

        function fire(particleRatio, opts) {
          confetti(Object.assign({}, defaults, opts, {
            particleCount: Math.floor(count * particleRatio)
          }));
        }

        fire(0.25, { spread: 26, startVelocity: 55 });
        fire(0.2, { spread: 60 });
        fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
        fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
        fire(0.1, { spread: 120, startVelocity: 45 });
    </script>
    """
    components.html(confetti_js, height=1)

# --- [2. 세션 및 설정] ---
if 'chef_result' not in st.session_state:
    st.session_state.chef_result = None
if 'unlocked' not in st.session_state:
    st.session_state.unlocked = False

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ API 키 설정이 필요합니다요! Secrets를 확인해 주셔요.")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [3. 디자인 스타일] ---
st.markdown("""
    <style>
    .main-title { font-size: 2.8rem; font-weight: 800; color: #111827; text-align: center; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background-color: #111827; color: white; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 12px; background-color: #059669; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- [4. PDF 생성기] ---
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

# --- [5. 메인 UI 및 분석 로직] ---
st.markdown('<p class="main-title">👨‍🍳 Microhard AI 흑백요리사</p>', unsafe_allow_html=True)
st.info("💡 냉장고 사진을 올리고 '대결 시작'을 누르면 화려한 축제와 함께 레시피가 공개됩니다요!")

uploaded_img = st.file_uploader("📸 냉장고 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, caption="분석 대기 중인 재료", use_container_width=True)
    
    if st.button("🔥 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 검토하고 있습니다요...", expanded=True) as status:
            try:
                # 모델은 안정적인 1.5-flash를 사용합니다요!
                model = genai.GenerativeModel('gemini-1.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
                prompt = "식재료를 분석해 백수저(영양), 흑수저(맛) 레시피를 작성해줘. 마크다운 기호 없이!"
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                status.update(label="✅ 분석 완료! 결투 결과가 나왔습니다요!", state="complete", expanded=False)
                
                # 결과 나오자마자 풍선+폭죽 동시 가동!
                play_celebration()
                
            except Exception as e:
                st.error(f"오류 발생: {e}")

# --- [6. 결과 출력 및 프리미엄 영역] ---
if st.session_state.chef_result:
    st.divider()
    st.subheader("🏁 AI 셰프들의 요리 제안")
    st.write(st.session_state.chef_result)
    
    st.divider()
    input_pw = st.text_input("🔑 리포트 잠금해제 (style77)", type="password")
    
    if input_pw == "style77":
        if not st.session_state.unlocked:
            play_celebration() # 비밀번호 맞으면 한 번 더 축하!
            st.session_state.unlocked = True
            
        pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
        st.download_button(
            label="📄 흑백요리사 식단 리포트 다운로드",
            data=bytes(pdf_bytes),
            file_name=f"Chef_Report.pdf",
            mime="application/pdf"
        )
