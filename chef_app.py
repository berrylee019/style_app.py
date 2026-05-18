import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import requests
from requests.auth import HTTPBasicAuth
import streamlit.components.v1 as components
import markdown # 상단에 추가
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- [구글 시트에서 미포스팅 목록 가져오기] ---
def get_pending_recipes():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("AI_Chef_Contents").sheet1
        all_records = sheet.get_all_records()
        
        # '포스팅여부'가 'No'인 행만 필터링 (행 번호도 같이 저장해야 나중에 'Yes'로 바꿀 수 있어유!)
        pending = []
        for i, row in enumerate(all_records):
            if row.get('포스팅여부') == 'No':
                row['row_idx'] = i + 2 # 헤더가 1번이라 데이터는 2번부터 시작!
                pending.append(row)
        return pending, sheet
    except Exception as e:
        st.error(f"시트 읽기 실패: {e}")
        return [], None
        
# --- [구글 시트 기록 함수] ---
def save_to_google_sheet(ingredients, title, content):
    try:
        # 1. 인증 정보 설정 (Secrets의 GCP_SERVICE_ACCOUNT 사용)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        
        # 2. 시트 열기 (정확한 시트 이름 입력!)
        sheet = client.open("AI_Chef_Contents").sheet1
        
        # 3. 기록할 데이터 준비
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 날짜, 재료, 제목, 내용, 포스팅여부(No) 순서입니다요.
        row = [now, ingredients, title, content, "No"]
        
        sheet.append_row(row)
        return True
    except Exception as e:
        # 시트 저장은 사용자에게 에러를 보여줄 필요까진 없으니 로그만 남깁니다요.
        print(f"시트 기록 실패: {e}")
        return False

# --- [GitHub Issues 구독 예약자 연동 함수] ---
def save_to_github_issues(email):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo_owner = st.secrets["GITHUB_REPO_OWNER"]
        repo_name = st.secrets["GITHUB_REPO_NAME"]
        
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # 다른 서비스와 섞이지 않도록 명확한 구분 타이틀 및 본문 세팅
        title = f"🚀 [AI 흑백요리사 Pro] 월 구독 사전 예약 신청 ({email})"
        body = f"""### 👨‍🍳 AI 흑백요리사 Pro 월 구독 사전 예약
---
- **혜택을 받으실 이메일:** {email}
- **신청 상품:** 월 9,900원 요금제 (사전 예약 50% 할인 대상)
- **접수 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---
*본 이슈는 'AI 흑백요리사' 솔라매니저 스타일 구독 폼을 통해 자동 생성되었습니다.*"""
        
        payload = {
            "title": title,
            "body": body,
            "labels": ["bw-chef-pro", "subscription-pre-order"]
        }
        
        res = requests.post(url, headers=headers, json=payload)
        return res.status_code == 201
    except Exception as e:
        st.error(f"깃허브 전송 중 오류 발생: {e}")
        return False

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
if 'paid' not in st.session_state: st.session_state.paid = False 

st.set_page_config(page_title="AI 흑백요리사", page_icon="👨‍🍳", layout="centered")

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ API 키가 설정되지 않았습니다. Secrets를 확인해 주셔요!")

# --- [5. 메인 UI] ---
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .main { background-color: #0f172a; color: #f8fafc; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background: linear-gradient(45deg, #1e293b, #334155);
        color: white;
        border: 1px solid #475569;
        font-weight: bold;
        padding: 0.6rem;
    }
    .stButton>button:hover { background: #475569; border-color: #94a3b8; }
    
    /* 카드 스타일 컨테이너 */
    .report-card {
        background-color: #1e293b;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #334155;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    /* 네이버 카페 안내 박스 */
    .cafe-notice {
        background-color: #064e3b;
        color: #ecfdf5;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #10b981;
        margin-bottom: 15px;
        font-size: 14px;
    }

    /* 솔라매니저 스타일: 상단 Pro 시작 버튼 컴포넌트 */
    .sol-pro-badge {
        display: inline-block;
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #e2e8f0;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* 솔라매니저 스타일: 파란색 사전 예약 안내 문구 */
    .sol-notice-box {
        background-color: #ebf5ff;
        color: #1e40af;
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 14.5px;
        font-weight: 500;
        margin-bottom: 15px;
    }
    /* 박스 테두리 컨테이너 */
    .sol-form-container {
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        color: #333333;
    }
    </style>
""", unsafe_allow_html=True)

# --- [메인 헤더 및 상단 이미지 정렬 섹션] ---
img_bot_col1, img_bot_col2, img_bot_col3 = st.columns([1, 8, 1])
with img_bot_col2:
    if os.path.exists("chef2.png"):
        st.image("chef2.png", use_container_width=True)
    else:
        st.image("chef2.png", use_container_width=True)

st.markdown('<div style="text-align: center; padding: 1rem 0;">', unsafe_allow_html=True)
st.markdown('<h1 style="font-size: 2.5rem; font-weight: 800; color: #475569;">👨‍🍳 AI 흑백요리사(영양사)</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #94a3b8; font-size: 1.1rem;">당신의 냉장고 사진 한 장으로 시작되는 미식 대결</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
    
uploaded_img = st.file_uploader("📸 냉장고 사진 업로드", type=["jpg", "jpeg", "png"])

if uploaded_img:
    st.image(uploaded_img, use_container_width=True)
    if st.button("🔥 레시피 대결 시작!"):
        with st.status("👨‍🍳 셰프들이 재료를 분석하고 있습니다...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                img_data = uploaded_img.read()
                img_part = {"mime_type": uploaded_img.type, "data": img_data}
                
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
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("🏁 AI 셰프들의 요리 제안")
    st.write(st.session_state.chef_result)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 📢 네이버 카페 가입 유도 안내
    st.markdown(f"""
        <div class="cafe-notice">
            📢 <b>비밀번호 발급 안내</b><br>
            <a href="https://cafe.naver.com/stylely" target="_blank" style="color: #6ee7b7; text-decoration: underline;">네이버 카페 '스타일리'</a>에 가입하시면 PDF 리포트 다운로드를 위한 비밀번호를 바로 확인(공지 참조)하실 수 있습니다!
        </div>
    """, unsafe_allow_html=True)
    
    # 🔑 비밀번호 입력창
    access_key = st.text_input("🔑 서비스 코드 입력", type="password", placeholder="카페에서 확인한 코드를 입력해 주세요")

    col1, col2 = st.columns(2)

    # A. 일반 회원 모드
    if access_key == "style77":
        if not st.session_state.paid:
            st.markdown("""
                <div style="background-color: #FEE500; color: #222222; padding: 18px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #EAEAEA;">
                    <h4 style="margin: 0 0 8px 0; font-weight: 800; font-size: 16px; display: flex; align-items: center;">
                        📱 카카오페이 / 계좌 결제 후 다운로드
                    </h4>
                    <p style="font-size: 13.5px; margin: 0; line-height: 1.5; color: #333333;">
                        본 식단 분석 리포트는 프리미엄 유료 서비스입니다.<br>
                        <b>결제 금액 : 3,000원</b><br>
                        아래 계좌 또는 카카오페이로 송금 후 결제 완료 버튼을 눌러주셔요!
                    </p>
                    <div style="background-color: #ffffff; padding: 10px; border-radius: 8px; margin-top: 12px; font-weight: bold; text-align: center; color: #111111; font-size: 14px; border: 1px solid #DDD;">
                        카카오뱅크 3333-01-0447508 (예금주: 이병서)
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with col1:
                if st.button("✅ 결제 및 송금을 완료했습니다"):
                    st.session_state.paid = True
                    st.rerun()
                    
        else:
            with col1:
                pdf_bytes = create_recipe_pdf(st.session_state.chef_result)
                st.download_button(label="📄 식단 리포트 PDF 저장", data=bytes(pdf_bytes), file_name="Chef_Report.pdf", mime="application/pdf")
            st.success("✅ 결제가 확인되었습니다! 회원님, 오늘의 맞춤 리포트를 다운로드 하셔요.")

    # B. 관리자(형님) 모드 (master77 입력 시)
    elif access_key == "master77":
        st.warning("😎 관리자 전용: 콘텐츠 곡간(구글 시트) 관리 모드")
        
        if st.button("📦 곡간에서 미발행 레시피 불러오기"):
            pending_list, sheet = get_pending_recipes()
            st.session_state.pending_recipes = pending_list
            st.success(f"총 {len(pending_list)}개의 새 레시피를 찾았습니다요!")

        if 'pending_recipes' in st.session_state and st.session_state.pending_recipes:
            for idx, item in enumerate(st.session_state.pending_recipes):
                with st.expander(f"📌 [{item['날짜']}] {item['레시피제목']}"):
                    st.write(f"**분석된 재료:** {item['분석된재료']}")
                    st.markdown("---")
                    new_title = st.text_input(f"제목 수정 ({idx})", value=item['레시피제목'], key=f"title_{idx}")
                    new_content = st.text_area(f"본문 수정 ({idx})", value=item['레시피내용'], height=200, key=f"content_{idx}")
                    
                    if st.button(f"🚀 이 글 바로 포스팅하기 ({idx})", key=f"btn_{idx}"):
                        with st.spinner("워드프레스 전송 및 시트 업데이트 중..."):
                            success = post_to_wordpress_pro(new_title, new_content, None) 
                            if success:
                                _, sheet = get_pending_recipes()
                                sheet.update_cell(item['row_idx'], 5, "Yes")
                                st.success("💰 포스팅 성공 및 곡간 업데이트 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 포스팅 실패. 로그를 확인하셔요.")

    # C. ✨ 신규: 솔라매니저 AI 스타일 월 구독형 사전 예약 UI (2.png 반영)
    if access_key not in ["style77", "master77"]:
        # 1. 상단 배지 노출
        st.markdown('<div class="sol-pro-badge">월 9,900원에 Pro 시작하기</div>', unsafe_allow_html=True)
        
        # 2. 파란색 알림 박스 노출
        st.markdown('<div class="sol-notice-box">현재 Pro 버전은 사전 예약 중입니다. 특별 혜택을 놓치지 마세요!</div>', unsafe_allow_html=True)
        
        # 3. 이메일 전용 입력 테두리 컨테이너 폼
        with st.container():
            st.markdown('<div style="color: #333333; font-weight: 500; font-size: 14px; margin-bottom: 5px;">혜택을 받으실 이메일</div>', unsafe_allow_html=True)
            p_email = st.text_input("혜택을 받으실 이메일", placeholder="example@email.com", key="premium_email", label_visibility="collapsed")
            
            st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
            
            if st.button("사전 예약하고 50% 할인받기"):
                if not p_email.strip():
                    st.error("❌ 이메일 주소를 입력해 주셔요!")
                elif "@" not in p_email:
                    st.error("❌ 올바른 이메일 형식이 아닙니다.")
                else:
                    with st.spinner("예약 신청 정보를 전송 중입니다..."):
                        success = save_to_github_issues(p_email)
                        if success:
                            # 2.png와 똑같은 형태의 초록색 완료 배지 효과 디자인
                            st.markdown("""
                                <div style="background-color: #e6f4ea; color: #137333; padding: 12px; border-radius: 6px; font-weight: bold; margin-top: 15px; font-size: 15px;">
                                    ✅ 예약 완료!
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("❌ 등록에 실패했습니다. 관리자 Secrets 세팅(GITHUB_TOKEN 등)을 확인해 주셔요.")
