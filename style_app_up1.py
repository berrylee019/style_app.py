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

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# --- [함수] 네이버 쇼핑 API (각 아이템별 개별 호출) ---
def get_single_product(gender, keyword):
    # 반대 성별을 제외하고 검색어 최적화
    exclude_gender = "남성" if gender == "여성" else "여성"
    refined_query = f"{gender} {keyword} -{exclude_gender}"
    
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

# --- [함수] 4개의 서로 다른 쇼핑 키워드 추출 ---
def extract_keywords_list(text):
    # 정규식으로 [# 쇼핑 키워드: [A, B, C, D]] 형태 추출
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        k_list = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return k_list[:4] # 최대 4개
    return ["트렌디 자켓", "패션 팬츠", "스타일리시 슈즈", "포인트 액세서리"]

# --- UI ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown(f"##### 형님({COUPANG_AF_ID}), 영상 한 번만 올리시면 수익형 아이템 4개를 바로 꽂아드립니다.")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("분석 성별", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] AI 분석 ---
if uploaded_file:
    if st.button("1단계: AI 스타일 정밀 분석", key="analysis_btn"):
        with st.spinner("AI 스타일리스트가 분석 중입니다..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # 4개의 개별 아이템을 명확히 뽑도록 유도
                prompt = f"""
                영상 속 인물의 패션 스타일을 분석해서 리포트를 작성해줘.
                성별: {gender}
                마지막 줄에 반드시 아래 형식을 지켜서 서로 다른 아이템 키워드 4개를 뽑아줘:
                # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 가방]
                """
                
                response = model.generate_content([
                    prompt, {"mime_type": "video/mp4", "data": video_data}
                ])
                
                st.session_state['analysis_result'] = response.text
                st.session_state['target_keywords'] = extract_keywords_list(response.text)
                st.session_state['analysis_done'] = True
                st.rerun()
            except Exception as e:
                st.error(f"분석 오류: {e}")

# --- [STEP 2] 리포트 & 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 아이템 4종 매칭하기", key="matching_btn"):
        with st.spinner("아이템별로 최적의 상품을 찾는 중..."):
            keywords = st.session_state.get('target_keywords', [])
            matched_items = []
            
            for kw in keywords:
                product = get_single_product(gender, kw)
                if product:
                    matched_items.append(product)
            
            st.session_state['final_products'] = matched_items
            st.session_state['products_done'] = True
            st.rerun()

# --- [STEP 3] 상품 카드 전시 (수익 링크 핵심) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 맞춤 추천 아이템 4선")
    
    items = st.session_state.get('final_products', [])
    if items:
        cols = st.columns(len(items))
        for i, item in enumerate(items):
            with cols[i]:
                with st.container(border=True):
                    # 제목 정화
                    title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{title[:18]}...**")
                    st.markdown(f"**{int(item['lprice']):,}원**")
                    
                    # [수익화 링크 해결]
                    # 단순 검색 URL이 아니라 형님의 ID를 태우는 '다이내믹 커스텀 링크' 구조입니다.
                    # 이 주소는 클릭 시 형님의 파트너스 ID를 인식하며 개별 검색어로 연결됩니다.
                    search_query = urllib.parse.quote(f"{gender} {title[:10]}")
                    coupang_url = f"https://link.coupang.com/a/custom?q={search_query}&account={COUPANG_AF_ID}"
                    
                    st.link_button("🔥 쿠팡 최저가 확인", coupang_url, use_container_width=True, type="primary")

    st.markdown("---")
    st.caption(f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
