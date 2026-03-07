import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import requests
from requests.auth import HTTPBasicAuth
import streamlit.components.v1 as components

# --- [1. 워드프레스 포스팅 함수] ---
def post_to_wordpress(title, content):
    try:
        # Secrets에서 정보를 가져옵니다요 (보안을 위해 나중에 입력하셔요!)
        wp_url = f"{st.secrets['WP_URL']}/wp-json/wp/v2/posts"
        user = st.secrets["WP_USER"]
        app_pw = st.secrets["WP_APP_PW"]
        
        payload = {
            "title": title,
            "content": content,
            "status": "publish" # 바로 발행!
        }
        
        res = requests.post(wp_url, auth=HTTPBasicAuth(user, app_pw), json=payload)
        return res.status_code == 201
    except Exception as e:
        st.error(f"워드프레스 통신 오류: {e}")
        return False

# --- [2. 축하 시스템 & 기타 설정] ---
def play_celebration():
    st.balloons()
    confetti_js = """<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script><script>var count = 200; var defaults = { origin: { y: 0.7 }, zIndex: 10000 }; function fire(particleRatio, opts) { confetti(Object.assign({}, defaults, opts, { particleCount: Math.floor(count * particleRatio) })); } fire(0.25, { spread: 26, startVelocity: 55 }); fire(0.2, { spread: 60 }); fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 }); fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 }); fire(0.1, { spread: 120, startVelocity: 45 });</script>"""
    components.html(confetti_js, height=1)

if 'chef_result' not in st.session_state: st.session_state.chef_result = None
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ API 키 설정 확인 필요!")

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

# --- [3. 메인 UI] ---
st.markdown('<h1 style="text-align: center;">👨‍🍳 Microhard AI 흑백요리사</h1>', unsafe_allow_html=True)
uploaded_img = st.file_uploader("📸 냉장고 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, use_container_width=True)
    if st.button("🔥 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 분석 중...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                # 수익형 블로그를 위해 SEO에 유리한 형식을 AI에게 지시합니다요!
                prompt = "냉장고 재료로 만드는 영양 백수저 vs 맛 흑수저 레시피. 블로그 포스팅용으로 제목과 본문을 구분해서 상세히 작성해줘."
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                play_celebration()
            except Exception as e:
                st.error(f"🚨 오류 발생: {e}")

if st.session_state.chef_result:
    st.divider()
    st.subheader("🏁 AI 셰프들의 요리 제안")
    st.write(st.session_state.chef_result)
    
    # --- [💰 수익형 자동화 버튼 섹션] ---
    st.info("📢 이 레시피를 바로 워드프레스에 포스팅할 수 있습니다요!")
    blog_title = st.text_input("블로그 제목", value="AI가 제안하는 오늘 냉장고 파먹기 레시피")
    
    if st.button("🚀 워드프레스에 즉시 포스팅하기"):
        with st.spinner("블로그 전송 중..."):
            success = post_to_wordpress(blog_title, st.session_state.chef_result)
            if success:
                st.success("✅ 형님! 워드프레스에 글이 성공적으로 올라갔습니다요! 애드센스 대박 나셔요! 💰")
                play_celebration()
            else:
                st.error("❌ 포스팅 실패. Secrets 설정을 확인해 주셔요.")
