import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import streamlit.components.v1 as components

# --- [1. 축하 시스템] ---
def play_celebration():
    st.balloons()
    confetti_js = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        var count = 200;
        var defaults = { origin: { y: 0.7 }, zIndex: 10000 };
        function fire(particleRatio, opts) {
          confetti(Object.assign({}, defaults, opts, { particleCount: Math.floor(count * particleRatio) }));
        }
        fire(0.25, { spread: 26, startVelocity: 55 });
        fire(0.2, { spread: 60 });
        fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
        fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
        fire(0.1, { spread: 120, startVelocity: 45 });
    </script>
    """
    components.html(confetti_js, height=1)

# --- [2. 설정] ---
if 'chef_result' not in st.session_state: st.session_state.chef_result = None
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

try:
    # API 키 설정
    api_key = st.secrets["MY_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ API 키 설정 확인 필요: {e}")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [3. PDF 생성기] ---
def create_recipe_pdf(content):
    def clean_text(text): return re.sub(r'\*\*|\*|__|#', '', text).strip()
    pdf = FPDF()
    pdf.add_page()
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else: pdf.set_font("Arial", size=12)
    pdf.set_fill_color(17, 24, 39); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font(pdf.font_family, size=20); pdf.text(15, 25, "AI BLACK & WHITE CHEF REPORT")
    pdf.set_y(50); pdf.set_text_color(31, 41, 55); pdf.set_font(pdf.font_family, size=11); pdf.multi_cell(0, 8, txt=clean_text(content))
    return pdf.output()

# --- [4. 메인 UI] ---
st.markdown('<h1 style="text-align: center;">👨‍🍳 Microhard AI 흑백요리사</h1>', unsafe_allow_html=True)
uploaded_img = st.file_uploader("📸 냉장고 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, use_container_width=True)
    if st.button("🔥 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 분석 중...", expanded=True) as status:
            try:
                # ✅ 가장 호환성 높은 모델명으로 호출합니다요!
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                prompt = "사진 속 재료를 분석해서 영양 위주의 백수저 레시피와 맛 위주의 흑수저 레시피를 제안해줘. 마크다운 기호 없이!"
                
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                play_celebration()
            except Exception as e:
                st.error(f"🚨 모델 호출 오류: {e}")
                st.info("💡 해결법: 깃허브의 requirements.txt 파일에 google-generativeai>=0.7.0 를 추가해 보셔요!")

if st.session_state.chef_result:
    st.divider(); st.subheader("🏁 AI 셰프들의 요리 제안"); st.write(st.session_state.chef_result)
    input_pw = st.text_input("🔑 리포트 잠금해제 (style77)", type="password")
    if input_pw == "style77":
        if not st.session_state.unlocked:
            play_celebration(); st.session_state.unlocked = True
        pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
        st.download_button(label="📄 PDF 리포트 다운로드", data=bytes(pdf_bytes), file_name="Chef_Report.pdf", mime="application/pdf")
