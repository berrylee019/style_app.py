import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. 환경 설정 및 API 키 확인
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
    
    # [수익화 핵심] 형님의 쿠팡 파트너스 ID
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! .streamlit/secrets.toml 파일을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# --- [함수] 네이버 쇼핑 API (성별 격리 검색 엔진) ---
def get_naver_products(gender, keyword):
    # 검색 단계에서 반대 성별을 아예 배제 (-) 합니다.
    exclude_gender = "남성" if gender == "여성" else "여성"
    refined_query = f"{gender} {keyword} -{exclude_gender}"
    
    encoded_keyword = urllib.parse.quote(refined_query)
    # 각 키워드당 가장 정확한 1개만 가져옵니다.
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

# --- [함수] 4개의 개별 아이템 키워드 추출 ---
def extract_keywords_list(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        k_list = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return k_list[:4]
    return ["트렌디 상의", "슬림핏 하의", "데일리 슈즈", "패션 잡화"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown(f"##### 형님({COUPANG_AF_ID})의 수익형 퍼스널 쇼퍼 AI")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 ---
if uploaded_file:
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일 분석 중..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 4개의 서로 다른 아이템을 명확히 리스트화 하도록 지시
                prompt = f"""
                영상 속 인물의 스타일을 분석해서 패션 리포트를 작성해줘. 성별: {gender}
                마지막에는 반드시 아래 형식을 지켜서 4개의 서로 다른 아이템 키워드를 뽑아줘:
                # 쇼핑 키워드: [{gender} 자켓, {gender} 바지, {gender} 신발, {gender} 가방]
                """
                
                response = model.generate_content([
                    prompt, {"mime_type": "video/mp4", "data": video_data}
                ])
                
                st.session_state['analysis_result'] = response.text
                st.session_state['search_keywords'] = extract_keywords_list(response.text)
                st.session_state['analysis_done'] = True
                st.rerun()
            except Exception as e:
                st.error(f"분석 에러: {e}")

# --- [STEP 2] 리포트 및 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 4종 실시간 매칭", key="matching_step_btn"):
        with st.spinner("아이템별 최적 상품 매칭 중..."):
            keywords = st.session_state.get('search_keywords', [])
            matched_products = []
            
            for kw in keywords:
                res = get_naver_products(gender, kw)
                if res: matched_products.append(res)
            
            st.session_state['final_products'] = matched_products
            st.session_state['products_done'] = True
            st.rerun()

# --- [STEP 3] 최종 상품 카드 (진짜 수익화 링크 적용) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 스타일 추천 아이템 4종")

    products = st.session_state.get('final_products', [])
    
    if products:
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 제목 정화 및 성별 재검증
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{clean_title[:15]}...**")
                    st.markdown(f"**{int(item['lprice']):,}원**")
                    
                    # --- [수익화 핵심 수술 부위] ---
                    # 1. 검색어 최적화 (성별 포함)
                    search_term = urllib.parse.quote(f"{gender} {clean_title[:10]}")
                    
                    # 2. [중요] 쿠팡 파트너스 '커스텀 검색 링크' 구조입니다.
                    # 이 URL은 클릭 시 형님의 수익 ID(account)를 시스템에 등록하고 해당 검색어로 연결합니다.
                    affiliate_url = f"https://link.coupang.com/a/custom?q={search_term}&account={COUPANG_AF_ID}"
                    
                    st.link_button("🔥 쿠팡 최저가 확인", affiliate_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
