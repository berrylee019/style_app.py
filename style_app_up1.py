import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# ==========================================
# 1. 형님의 고유 설정 (여기만 확인하세요!)
# ==========================================
NAVER_ID = "CS3M6p8wqe7L4t1W4pbW"
NAVER_SECRET = "uh542B_0BS"
MY_REVENUE_LINK = "https://link.inpock.co.kr/shopping1" # 형님의 인포크 주소

# Secrets에서 Gemini API 키 가져오기
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except Exception as e:
    st.error(f"⚠️ Secrets 설정 오류: MY_API_KEY가 없습니다. {e}")

# Streamlit 기본 설정 (와이드 모드)
st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# ==========================================
# 2. 비주얼 커스텀 스타일링 (디자인 핵심)
# ==========================================
st.markdown("""
<style>
    /* 전체 배경색 및 기본 폰트 */
    .stApp { background-color: #F9FAFB; font-family: 'Pretendard', sans-serif; }

    /* 대제목 스타일 */
    .stApp h1 { color: #1E3A8A; font-weight: 800; text-align: center; }

    /* 서브 텍스트 스타일 */
    .stApp h5 { color: #6B7280; text-align: center; margin-top: -10px; }

    /* 캡션 텍스트 (블루 포인트) */
    .point-text { color: #2563EB; font-weight: 600; text-align: center; }

    /* 결과 리포트 영역 스타일 */
    .stInfo { background-color: #DBEAFE !important; border-radius: 12px; color: #1E40AF !important; }

    /* 상품 카드 컨테이너 */
    [data-testid="stContainer"] { border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }

    /* 수익 버튼 전용 스타일 */
    .stButton > button { background-color: #2563EB !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# --- [함수] 네이버 쇼핑 API (성별 고립 검색 엔진) ---
def get_strictly_gender_item(gender, keyword):
    # 반대 성별 키워드를 마이너스(-) 처리하여 섞임 방지
    exclude = "남성" if gender == "여성" else "여성"
    # 예: "여성 코트 -남성 -공용 -남녀공용"
    refined_query = f"{gender}용 {keyword} -{exclude} -공용 -남녀공용"
    
    encoded_keyword = urllib.parse.quote(refined_query)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_keyword}&display=1&sort=sim"
    
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get('items', [])
            return items[0] if items else None
        return None
    except:
        return None

# --- [함수] 4개 아이템 키워드 정밀 추출 ---
def extract_4_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        k_list = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return k_list[:4] # 최대 4개
    return ["상의", "하의", "신발", "가방"]

# ==========================================
# 3. 메인 UI 레이아웃
# ==========================================
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("<h5>실시간 비디오 분석으로 완성하는 당신만의 퍼스널 룩</h5>", unsafe_allow_html=True)
st.markdown("---")

# --- [STEP 1] 촬영 가이드 및 업로드 섹션 (최고의 비주얼 디자인) ---
st.markdown("<p class='point-text'>📽️ 분석을 시작하려면 전신 샷 필수!</p>", unsafe_allow_html=True)
st.markdown("##### 오늘의 베스트 룩을 찾아드릴게요!")
st.divider()

col_guide, col_upload = st.columns([1.5, 1])

with col_guide:
    # 촬영 가이드 디자인 섹션 (형님이 보내주신 디자인 완벽 구현)
    st.markdown("#### 📺 가이드 영상 보기")
    # Streamlit에서 로컬 비디오 재생 (secrets.toml에 파일 주소 설정 권장)
    try:
        with open("sample_guide.mp4", 'rb') as video_file:
            video_bytes = video_file.read()
        st.video(video_bytes, format='video/mp4', start_time=0)
    except:
        st.warning("⚠️ 'sample_guide.mp4' 파일을 찾을 수 없습니다. (디자인 예시용)")
        st.image("https://via.placeholder.com/800x450.png?text=Sample+Video+Placeholder", use_container_width=True)

with col_upload:
    st.markdown("#### 🎬 영상을 업로드하세요")
    uploaded_file = st.file_uploader("", type=["mp4", "mov"])
    st.markdown("##### limit 200MB per file / MP4, MOV, AVI")
    st.caption(" 너무 길면 업로드가 느려질 수 있어요. (5~15초 권장)")

st.divider()

# 분석 실행 버튼
gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
if uploaded_file and st.button("🚀 스타일 분석 및 수익 아이템 매칭 시작"):
    with st.spinner("AI가 영상을 분석하고 성별에 맞는 아이템을 매칭 중입니다..."):
        try:
            # 1. Gemini 영상 분석
            video_data = uploaded_file.read()
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            영상 속 스타일을 분석해서 패션 리포트를 작성해줘. 대상은 반드시 '{gender}'이야.
            마지막 줄에 반드시 이 형식을 지켜서 서로 다른 4개 아이템을 뽑아줘:
            # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 액세서리]
            """
            response = model.generate_content([prompt, {"mime_type": "video/mp4", "data": video_data}])
            
            # 2. 결과 저장 및 키워드 추출
            analysis_text = response.text
            keywords = extract_4_keywords(analysis_text)
            
            # 3. 네이버 API 개별 호출 (4회)
            final_products = []
            for kw in keywords:
                prod = get_strictly_gender_item(gender, kw)
                if prod: final_products.append(prod)
            
            # --- 분석 결과 리포트 ---
            st.divider()
            st.subheader("📊 AI 스타일 분석 리포트")
            st.info(analysis_text)
            st.divider()
            
            # --- 상품 카드 전시 영역 ---
            st.subheader(f"🛒 추천 {gender} 아이템 4선")
            cols = st.columns(len(final_products))
            
            for i, item in enumerate(final_products):
                with cols[i]:
                    with st.container(border=True):
                        # 제목 정화 (HTML 제거)
                        title = item['title'].replace('<b>', '').replace('</b>', '')
                        # 이미지 및 정보
                        st.image(item['image'], use_container_width=True)
                        st.markdown(f"**{title[:15]}...**")
                        st.markdown(f"**{int(item['lprice']):,}원**")
                        
                        # [가장 중요] 수익화 링크 (형님의 인포크 주소로 강제 직결!)
                        # item['link'] 대신 형님의 수익 링크를 강제로 넣었습니다.
                        st.link_button(
                            label="🔥 최저가 혜택받기", 
                            url=MY_REVENUE_LINK, 
                            use_container_width=True, 
                            type="primary"
                        )
                        st.caption("※ 클릭 시 형님의 인포크 혜택 페이지로 이동합니다.")

            st.success(f"형님, 모든 추천 상품 버튼이 인포크링크({MY_REVENUE_LINK})로 정확하게 연결되었습니다! 🚀🦾")

        except Exception as e:
            st.error(f"⚠️ 분석 중 오류 발생: {e}")
