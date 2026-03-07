import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import requests
from requests.auth import HTTPBasicAuth
import streamlit.components.v1 as components
import markdown # 상단에 추가

# --- [1. 수익형 본문 정제 및 링크 삽입 함수] ---
def inject_monetization(text):
    # 지저분한 구분선 먼저 제거
    clean_text = text.replace("---", "")
    
    # 쿠팡 파트너스 키워드 및 링크 (형님의 실제 링크로 교체하셔요!)
    coupang_keywords = {
        "프라이팬": "https://link.coupang.com/a/dZQtZs",
        "냄비": "https://link.coupang.com/a/dZQvKh",
        "칼": "https://link.coupang.com/a/dZQzJx",
        "에어프라이어": "https://link.coupang.com/a/dZQAN5",
        "믹서기": "https://link.coupang.com/a/dZQBq0"
    }
    
    # 본문 내 키워드에 수익형 링크 삽입
    for word, link in coupang_keywords.items():
        if word in clean_text:
            # 텍스트 내 단어를 링크가 포함된 형태로 치환
            replacement = f'<strong>{word}</strong> <a href="{link}" style="color: #ff4200; font-weight: bold; text-decoration: none;">[🛒 최저가 확인]</a>'
            clean_text = clean_text.replace(word, replacement)

    # 마크다운을 정갈한 HTML로 변환 (### -> <h2> 등)
    html_body = markdown.markdown(clean_text)
    
    # 하단 서비스 홍보 문구 추가
    footer_html = f"""
    <div style="margin-top: 50px; padding: 20px; border-top: 2px solid #f0f0f0; background-color: #f9f9f9; border-radius: 10px; text-align: center;">
        <p style="color: #555; font-size: 16px; margin-bottom: 10px;">👨‍🍳 <b>이 레시피는 AI 흑백요리사가 분석한 맞춤형 식단입니다.</b></p>
        <p style="color: #888; font-size: 14px; margin-bottom: 20px;">더 많은 맞춤형 레시피와 영양 분석 리포트를 원하신다면 아래 서비스에 방문해 보세요!</p>
        <a href="https://bw-chef.streamlit.app" style="display: inline-block; padding: 12px 25px; background-color: #111827; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold;">나도 냉장고 분석 받기 🚀</a>
    </div>
    """
    
    return f'<div class="recipe-post" style="line-height: 1.8; font-size: 16px;">{html_body}{footer_html}</div>'

# --- [2. 워드프레스 미디어 업로드 함수: 썸네일용] ---
def upload_wp_media(img_bytes, filename):
    try:
        wp_url = f"{st.secrets['WP_URL']}/wp-json/wp/v2/media"
        user = st.secrets["WP_USER"]
        app_pw = st.secrets["WP_APP_PW"]
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "image/jpeg"
        }
        
        res = requests.post(wp_url, auth=HTTPBasicAuth(user, app_pw), headers=headers, data=img_bytes)
        if res.status_code == 201:
            return res.json()['id'] # 업로드된 이미지 ID 반환
        return None
    except:
        return None

# --- [3. 최종 통합 포스팅 함수] ---
def post_to_wordpress_pro(title, content, img_bytes):
    try:
        # 본문 정제 및 수익화 작업
        final_html = inject_monetization(content)
        
        # 썸네일 업로드 시도
        media_id = upload_wp_media(img_bytes, "chef_thumbnail.jpg")
        
        # 워드프레스 글 발행
        wp_url = f"{st.secrets['WP_URL']}/wp-json/wp/v2/posts"
        user = st.secrets["WP_USER"]
        app_pw = st.secrets["WP_APP_PW"]
        
        payload = {
            "title": title,
            "content": final_html,
            "status": "publish",
            "featured_media": media_id if media_id else None
        }
        
        res = requests.post(wp_url, auth=HTTPBasicAuth(user, app_pw), json=payload)
        return res.status_code == 201
    except Exception as e:
        st.error(f"포스팅 오류: {e}")
        return False

# --- [2. 축하 시스템] ---
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
    
    # 헤더 디자인
    pdf.set_fill_color(17, 24, 39); pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font(pdf.font_family, size=20)
    pdf.text(15, 25, "AI BLACK & WHITE CHEF REPORT")
    
    # 본문
    pdf.set_y(50); pdf.set_text_color(31, 41, 55); pdf.set_font(pdf.font_family, size=11)
    pdf.multi_cell(0, 8, txt=clean_text(content))
    return pdf.output()

# --- [4. 초기 설정] ---
if 'chef_result' not in st.session_state: st.session_state.chef_result = None
if 'unlocked' not in st.session_state: st.session_state.unlocked = False

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ API 키가 설정되지 않았습니다. Secrets를 확인해 주셔요!")

# --- [5. 메인 UI] ---
st.markdown('<h1 style="text-align: center;">👨‍🍳 AI 흑백요리사(영양사)</h1>', unsafe_allow_html=True)
st.write("냉장고 속 남은 재료 사진을 올리면 AI 셰프들이 대결을 시작합니다!")

uploaded_img = st.file_uploader("📸 냉장고 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, use_container_width=True)
    if st.button("🔥 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 분석하고 있습니다...", expanded=True) as status:
            try:
                # 에러 방지를 위해 가장 안정적인 모델명 사용
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
                # 수익형 블로그를 고려한 프롬프트
                prompt = """사진 속 식재료를 분석해서 다음 양식으로 작성해줘:
                1. 분석된 식재료 리스트
                2. [백수저 레시피] - 건강과 영양 중심
                3. [흑수저 레시피] - 자극적이고 맛 중심
                4. 영양사 총평 (블로그 포스팅에 적합한 말투로 부탁해)"""
                
                response = model.generate_content([prompt, img_part])
                st.session_state.chef_result = response.text
                status.update(label="✅ 레시피 완성!", state="complete", expanded=False)
                play_celebration()
            except Exception as e:
                st.error(f"🚨 오류 발생: {e}")

# --- [6. 결과 및 권한 제어 영역] ---
if st.session_state.chef_result:
    st.divider()
    st.subheader("🏁 AI 셰프들의 요리 제안")
    st.write(st.session_state.chef_result)
    
    st.divider()
    # 비밀번호 입력창 (일반 회원: style77 / 형님: master77)
    access_key = st.text_input("🔑 서비스 코드 입력 (리포트/관리자)", type="password")

    col1, col2 = st.columns(2)

    # A. 일반 회원 모드
    if access_key == "style77":
        with col1:
            pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
            st.download_button(label="📄 식단 리포트 PDF 저장", data=bytes(pdf_bytes), file_name="Chef_Report.pdf", mime="application/pdf")
        st.success("✅ 회원님, 오늘의 맞춤 리포트가 준비되었습니다!")

    # B. 관리자(형님) 모드
    elif access_key == "master77":
        st.warning("😎 관리자 모드: 수익형 블로그 포스팅이 가능합니다.")
        with col1:
            pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
            st.download_button("📄 PDF 백업", data=bytes(pdf_bytes), file_name="Admin_Copy.pdf")
        
        with col2:
            blog_title = "AI가 제안하는 냉장고 파먹기 역전 레시피!"
            if st.button("🚀 워드프레스에 즉시 포스팅"):
                with st.spinner("포스팅 전송 중..."):
                    if post_to_wordpress(blog_title, st.session_state.chef_result):
                        st.success("💰 워드프레스 발행 성공! 수익 가즈아!")
                        play_celebration()
                    else:
                        st.error("❌ 발행 실패. 설정을 확인하셔요.")
