import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. 환경 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
    
    # [수익화] 형님의 쿠팡 파트너스 ID
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! .streamlit/secrets.toml 파일을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API (성별 고립 검색) ---
def get_naver_products(gender, keyword):
    # 검색어 자체에 성별을 강력하게 박고 반대 성별을 제외합니다.
    exclude_gender = "남성" if gender == "여성" else "여성"
    # 예: "여성용 트위드 자켓 -남성"
    refined_query = f"{gender}용 {keyword} -{exclude_gender}"
    
    encoded_keyword = urllib.parse.quote(refined_query)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_keyword}&display=1&sort=sim"
    
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

# --- [함수] 4개의 서로 다른 키워드 추출 ---
def extract_multiple_keywords(text):
    # # 쇼핑 키워드: [키워드1, 키워드2, 키워드3, 키워드4] 형식을 찾습니다.
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        raw_keywords = match.group(1).split(',')
        # 불필요한 공백과 특수문자 제거 후 4개 추출
        keywords = [k.strip().replace('[', '').replace(']', '') for k in raw_keywords]
        return keywords[:4]
    return ["트렌디 자켓", "슬랙스", "패션 스니커즈", "숄더백"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 당신의 스타일을 분석하여 4가지 맞춤 아이템을 제안합니다.")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("분석할 성별", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 스타일링 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 (Gemini 1.5) ---
if uploaded_file:
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일을 분석하고 키워드를 생성 중입니다..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # 4개의 서로 다른 아이템을 뽑아내도록 프롬프트 수정
                prompt = f"""
                영상 속 인물의 패션 스타일을 분석해줘. 성별은 반드시 '{gender}'이야.
                분석 결과 마지막 줄에 반드시 아래 형식을 지켜서 4개의 서로 다른 쇼핑 아이템을 추천해줘:
                # 쇼핑 키워드: [{gender} 자켓, {gender} 팬츠, {gender} 슈즈, {gender} 액세서리]
                """
                
                response = model.generate_content([
                    prompt,
                    {"mime_type": "video/mp4", "data": video_data}
                ])
                
                st.session_state['analysis_result'] = response.text
                st.session_state['search_keywords'] = extract_multiple_keywords(response.text)
                st.session_state['analysis_done'] = True
                st.rerun()
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")

# --- [STEP 2] 리포트 출력 및 아이템 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 4종 실시간 매칭", key="matching_step_btn"):
        with st.spinner("4가지 아이템을 각각 찾는 중..."):
            all_found_products = []
            keywords = st.session_state.get('search_keywords', [])
            
            for kw in keywords:
                # 각 키워드당 가장 유사한 상품 1개씩 수집 (총 4개)
                res = get_naver_products(gender, kw)
                if res:
                    all_found_products.append(res[0])
            
            if all_found_products:
                st.session_state['matched_products'] = all_found_products
                st.session_state['products_done'] = True
                st.rerun()
            else:
                st.warning("상품 정보를 찾지 못했습니다.")

# --- [STEP 3] 최종 상품 카드 (개별 수익 링크 & 성별 보장) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 스타일 맞춤 추천 아이템 (4종)")

    products = st.session_state.get('matched_products', [])
    
    if products:
        # 4개의 열을 만들어 나란히 배치
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 1. 이미지
                    st.image(item['image'], use_container_width=True)
                    
                    # 2. 제목 정화
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.markdown(f"**{clean_title[:15]}...**")
                    
                    # 3. 가격
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # --- [수익화 핵심: 버튼 실종 방지 및 개별 링크] ---
                    # 검색 키워드 생성 (성별 + 정제된 상품명)
                    search_term = f"{gender} {clean_title[:10]}"
                    encoded_search = urllib.parse.quote(search_term)
                    
                    # 쿠팡 파트너스 다이내믹 검색 URL (형님 ID AF5326630 적용)
                    # 이 구조는 각 버튼이 서로 다른 'search_term'을 쿠팡으로 던지게 만듭니다.
                    final_url = f"https://link.coupang.com/a/custom?q={encoded_search}&account={COUPANG_AF_ID}"
                    
                    # 버튼 생성 (이제 무조건 표시됩니다)
                    st.link_button("🔥 쿠팡 최저가", final_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
