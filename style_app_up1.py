import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. 환경 설정 및 수익화 정보
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
    
    # [수익화] 형님의 쿠팡 파트너스 ID
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! .streamlit/secrets.toml 파일을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API (성별 격리 필터 적용) ---
def get_naver_products(gender, keyword):
    # 반대 성별을 아예 검색 결과에서 제거하기 위한 제외(-) 검색어 활용
    exclude_gender = "남성" if gender == "여성" else "여성"
    # 예: "여성 오버핏 코트 -남성"
    refined_query = f"{gender} {keyword} -{exclude_gender}"
    
    encoded_keyword = urllib.parse.quote(refined_query)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_keyword}&display=4&sort=sim"
    
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('items', [])
        return []
    except:
        return []

# --- [함수] 리포트에서 키워드만 정밀 추출 ---
def extract_shop_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
    if match:
        keywords = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return keywords[0] if keywords else "트렌디 패션"
    return "트렌디 패션"

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 당신의 스타일을 분석하고 최적의 아이템을 개별 매칭합니다.")

# 세션 상태 초기화
if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 ---
if uploaded_file:
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일을 정밀 분석 중..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # 성별 지침을 아주 강력하게 강화
                prompt = f"""
                영상 속 인물의 패션 스타일을 분석해서 전문가 리포트를 써줘.
                사용자의 성별은 반드시 '{gender}'이야. 반드시 {gender} 카테고리 내에서만 분석해.
                분석 마지막에는 아래 형식을 포함해:
                # 쇼핑 키워드: [{gender} 스타일 키워드 하나]
                """
                
                response = model.generate_content([
                    prompt,
                    {"mime_type": "video/mp4", "data": video_data}
                ])
                
                st.session_state['analysis_result'] = response.text
                st.session_state['search_keyword'] = extract_shop_keywords(response.text)
                st.session_state['analysis_done'] = True
                st.rerun()
            except Exception as e:
                st.error(f"분석 에러: {e}")

# --- [STEP 2] 리포트 및 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 실시간 매칭", key="matching_step_btn"):
        # 검색 단계부터 성별 주입
        products = get_naver_products(gender, st.session_state.get('search_keyword', '패션'))
        if products:
            st.session_state['naver_products'] = products
            st.session_state['products_done'] = True
            st.rerun()
        else:
            st.warning("아이템을 찾지 못했습니다.")

# --- [STEP 3] 최종 상품 카드 (개별 수익 링크 완성본) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 스타일 추천 아이템")

    products = st.session_state.get('naver_products', [])
    
    if products:
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 1. 이미지
                    st.image(item['image'], use_container_width=True)
                    
                    # 2. 제목 정화 (HTML 태그 제거)
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    
                    # 3. [최종 검증] 제목에 반대 성별이 섞여있으면 출력 안 함
                    exclude_word = "남성" if gender == "여성" else "여성"
                    if exclude_word in clean_title and gender not in clean_title:
                        continue
                        
                    # 제목이 너무 길면 쿠팡 검색 품질이 떨어지므로 앞부분 위주로 사용
                    short_title = clean_title[:15].strip()
                    st.markdown(f"**{short_title}...**")
                    
                    # 4. 가격
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # --- [수익화 핵심: 다이내믹 커스텀 링크] ---
                    # 1. 검색어 준비 (성별 + 상품명)
                    search_query = urllib.parse.quote(f"{gender} {short_title}")
                    
                    # 2. 형님의 AF ID가 박히면서 동시에 검색어를 개별적으로 전달하는 '진짜' 수익 링크
                    # link.coupang.com/a/custom 구조는 q와 account 파라미터를 통해 
                    # 각각의 버튼이 다른 결과를 띄우게 만듭니다.
                    final_url = f"https://link.coupang.com/a/custom?q={search_query}&account={COUPANG_AF_ID}"
                    
                    st.link_button("🔥 쿠팡 최저가 확인", final_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 이 서비스는 쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
