import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime
import os
import re

# 1. API 키 및 페이지 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("API 키 설정이 필요합니다요! secrets.toml 확인 부탁드려유.")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [디자인] 흑백 테마 CSS ---
# --- [UI 개선 코드 조각] ---
st.markdown('<p class="main-title">👨‍🍳 Microhard AI 흑백요리사</p>', unsafe_allow_html=True)

# 전문가 가이드 영역
st.info("""
    **💡 이용 방법:**
    1. 냉장고 안의 재료가 잘 보이도록 촬영해 주세요.
    2. AI가 재료를 분석하여 **영양 중심(백수저)**과 **가성비(흑수저)** 레시피를 제안합니다.
    3. 형님의 체형 분석 데이터와 연동되어 최적의 칼로리를 계산해 드립니다.
""")

# 콜 투 액션(CTA) 강화
with st.expander("❓ 왜 AI 흑백요리사를 써야 하나요?"):
    st.write("- 낭비되는 식재료 제로(Zero Waste)")
    st.write("- 내 몸에 딱 맞는 탄/단/지 비율 계산")
    st.write("- 전문 요리사의 킥(Kick)이 담긴 레시피")

# --- [기능] 프리미엄 PDF 리포트 생성 (chef 버전) ---
def create_recipe_pdf(content):
    def clean_text(text):
        # 불필요한 마크다운 기호 완벽 제거
        text = re.sub(r'\*\*|\*|__|#', '', text)
        return text.strip()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    epw = pdf.w - 20
    
    font_path = "NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 12)
    else: pdf.set_font("Arial", size=12)

    # 헤더 디자인 (블랙 & 골드 느낌으로 고급화)
    pdf.set_fill_color(17, 24, 39) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Nanum', '', 20)
    pdf.text(15, 25, "AI BLACK & WHITE CHEF REPORT")
    
    pdf.set_y(50)
    pdf.set_text_color(31, 41, 55)
    
    # 본문 출력 (세탁기 돌린 텍스트)
    pdf.multi_cell(epw, 8, txt=clean_text(content))
    
    return pdf.output()

# --- [UI] 메인 화면 ---
st.markdown('<p class="main-title">👨‍🍳 AI 흑백요리사 (영양사)</p>', unsafe_allow_html=True)
st.write("냉장고 사진을 찍어 올리시면, 형님의 체형에 맞는 '생존 레시피'가 펼쳐집니다요!")

# --- [기능] 사진 업로드 및 분석 ---
uploaded_img = st.file_uploader("냉장고 재료 사진을 올려주셔요", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, caption="분석할 냉장고 재료", use_container_width=True)
    
    if st.button("🍴 레시피 대결 시작!"):
        with st.spinner("👨‍🍳 셰프들이 재료를 검토 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
                # 전문 영양 분석 및 흑백 대결 프롬프트
                prompt = """
                당신은 사진 속 식재료를 완벽히 식별하는 AI 흑백요리사 영양사입니다. 
                다음 순서로 리포트해 주세요 (마크다운 기호는 절대 쓰지 마세요):

                1. 식별된 재료 리스트: 사진에서 확인된 모든 재료를 나열하세요.
                
                2. [백수저 모드] - 영양 완벽형:
                - 보유 재료 중 가장 건강한 조합으로 조리법 제안.
                - 예상 칼로리와 탄/단/지 비율 수치화.
                - 체형 관리(다이어트) 포인트 설명.

                3. [흑수저 모드] - 맛과 속도 중심:
                - 가장 빠르고 맛있게 먹을 수 있는 자취생/서바이벌형 조리법.
                - 자극적이지 않으면서도 만족도가 높은 킥(Kick) 포인트 전수.

                전문적이고 자신감 넘치는 셰프의 톤으로 작성하세요.
                """
                
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                
            except Exception as e:
                st.error(f"오류 발생: {e}")

# --- [UI] 분석 결과 전시 ---
if 'chef_result' in st.session_state:
    st.divider()
    res = st.session_state.chef_result
    
    # 화면에는 백/흑 느낌 살려서 출력
    st.subheader("🏁 셰프들의 제안")
    st.markdown(res) # 화면에 출력

    # 비밀번호 및 PDF 다운로드
    input_pw = st.text_input("리포트 잠금해제 (style77)", type="password")
    if input_pw == "style77":
        pdf_bytes = create_recipe_pdf(res)
        st.download_button(
            label="📄 흑백요리사 식단 리포트 다운로드",
            data=bytes(pdf_bytes),
            file_name="Chef_Report.pdf",
            mime="application/pdf"
        )
