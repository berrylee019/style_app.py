import markdown # 상단에 추가

# --- [본문 정제 함수: 마크다운 기호 제거 및 스타일링] ---
def clean_post_content(text):
    # 1. 지저분한 기호들 제거/치환
    text = text.replace("---", "") # 구분선 제거
    # 2. 마크다운을 HTML로 변환 (### -> <h2>, ** -> <strong> 등)
    html = markdown.markdown(text)
    # 3. 추가적인 스타일링 (예: 폰트 크기나 강조 색상 입히기)
    styled_html = f"""
    <div style="line-height: 1.8; font-family: 'Nanum Gothic', sans-serif;">
        {html}
    </div>
    """
    return styled_html

# --- [워드프레스 미디어 업로드 함수: 썸네일용] ---
def upload_wp_media(img_bytes, filename):
    wp_url = f"{st.secrets['WP_URL']}/wp-json/wp/v2/media"
    user = st.secrets["WP_USER"]
    app_pw = st.secrets["WP_APP_PW"]
    
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "image/jpeg"
    }
    
    res = requests.post(wp_url, auth=HTTPBasicAuth(user, app_pw), headers=headers, data=img_bytes)
    if res.status_code == 201:
        return res.json()['id'] # 업로드된 이미지의 ID 반환
    return None

# --- [최종 워드프레스 포스팅 함수] ---
def post_to_wordpress_pro(title, content, img_bytes):
    try:
        # 1. 본문 정제
        clean_html = clean_post_content(content)
        
        # 2. 썸네일 업로드
        media_id = upload_wp_media(img_bytes, "chef_thumbnail.jpg")
        
        # 3. 글 발행
        wp_url = f"{st.secrets['WP_URL']}/wp-json/wp/v2/posts"
        user = st.secrets["WP_USER"]
        app_pw = st.secrets["WP_APP_PW"]
        
        payload = {
            "title": title,
            "content": clean_html,
            "status": "publish",
            "featured_media": media_id if media_id else None # 썸네일 지정!
        }
        
        res = requests.post(wp_url, auth=HTTPBasicAuth(user, app_pw), json=payload)
        return res.status_code == 201
    except Exception as e:
        st.error(f"포스팅 에러: {e}")
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
