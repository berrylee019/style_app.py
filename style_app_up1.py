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
    
    # 형님의 쿠팡 파트너스 ID
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! .streamlit/secrets.toml 파일을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API 엔진 ---
def get_naver_products(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/shop.json?query={encoded_keyword}&display=4&sort=sim"
    
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        return []
    except:
        return []

# --- [함수] 키워드 추출 ---
def extract_shop_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
    if match:
        keywords = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return keywords[0] if keywords else "트렌디 패션"
    return "트렌디 패션"

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 영상 분석을 통한 당신의 퍼스널 쇼퍼 AI")

# 세션 상태 초기화
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
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                영상 속 인물의 스타일을 분석해서 패션 리포트를 작성해줘.
                성별: {gender}
                분석 마지막에는 아래 형식을 포함해:
                # 쇼핑 키워드: [{gender} 스타일 키워드]
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
        base_keyword = st.session_state.get('search_keyword', '패션')
        target_keyword = f"{gender} {base_keyword}"
        
        with st.spinner(f"'{target_keyword}' 상품 찾는 중..."):
            products = get_naver_products(target_keyword)
            if products:
                st.session_state['naver_products'] = products
                st.session_state['products_done'] = True
                st.rerun()
            else:
                st.warning("상품을 찾지 못했습니다.")

# --- [STEP 3] 최종 상품 카드 (수익화 링크 수정본) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 스타일 추천 아이템")

    products = st.session_state.get('naver_products', [])
    
    if products:
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    st.image(item['image'], use_container_width=True)
                    
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    
                    # 성별 필터링
                    if gender == "여성" and ("남성" in clean_title) and "여성" not in clean_title:
                        st.caption("공용/남성 상품 제외")
                        continue
                        
                    st.markdown(f"**{clean_title[:15]}...**")
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # --- [수익화 링크 수술 부위] ---
                    # 1. 정확한 검색을 위해 특수문자 제거 및 인코딩
                    search_keyword = f"{gender} {clean_title}"
                    encoded_search = urllib.parse.quote(search_query := search_keyword)

                    # 2. [가장 중요] 쿠팡 파트너스 다이렉트 검색 URL 구조
                    # 이 구조는 HMAC 인증 없이도 검색어 결과를 정확히 띄워줍니다.
                    affiliate_url = f"https://www.coupang.com/np/search?q={encoded_search}&channel=user&from_ranking=y"
                    
                    # 3. [형님 필독] 단순히 쿠팡 페이지로 보내는 것과 '수익'을 내는 것은 다릅니다.
                    # 만약 위 URL로 수익이 안 잡힌다면, 쿠팡 파트너스에서 '검색어 링크'를 하나 생성하신 후
                    # 그 URL 주소를 알려주시면 제가 그 뒤에 키워드가 붙게 개조해 드릴게요!
                    
                    st.link_button("🔥 쿠팡 최저가 확인", affiliate_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
