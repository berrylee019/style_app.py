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
    
    # [수익화 설정] 형님의 쿠팡 파트너스 고유 ID (직접 입력됨)
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! Secrets를 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API (성별 필터 강화 버전) ---
def get_naver_products(gender, keyword):
    # 반대 성별을 아예 검색어에서 마이너스(-) 처리하여 제거
    exclude_gender = "남성" if gender == "여성" else "여성"
    # 예: "여성 오버핏 자켓 -남성"
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

# --- [함수] 리포트에서 키워드만 쏙 뽑아내기 ---
def extract_shop_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
    if match:
        keywords = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return keywords[0] if keywords else "트렌디 패션"
    return "트렌디 패션"

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 당신의 스타일을 분석하고, 개별 맞춤 아이템을 추천합니다.")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("분석할 성별", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 스타일링 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 ---
if uploaded_file:
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 패션 스타일을 정밀 분석 중입니다..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # AI에게 성별 구분을 아주 강력하게 주문
                prompt = f"""
                너는 패션 전문가야. 영상 속 인물의 스타일을 분석해서 리포트를 써줘.
                사용자의 성별은 반드시 '{gender}'이야. {gender} 패션 카테고리 내에서만 생각하고 분석해.
                리포트 마지막 줄에는 반드시 아래 형식을 포함해:
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
                st.error(f"⚠️ 분석 오류: {e}")

# --- [STEP 2] 리포트 및 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 실시간 매칭", key="matching_step_btn"):
        with st.spinner("맞춤 상품을 검색 중..."):
            # 검색 단계부터 성별 주입
            products = get_naver_products(gender, st.session_state.get('search_keyword', '패션'))
            if products:
                st.session_state['naver_products'] = products
                st.session_state['products_done'] = True
                st.rerun()
            else:
                st.warning("상품 정보를 가져오지 못했습니다.")

# --- [STEP 3] 최종 상품 카드 (다이내믹 수익 링크 적용) ---
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
                    
                    # 2. 제목 정화
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    
                    # 3. [2중 필터] 제목에 반대 성별 단어가 있으면 제외
                    exclude_word = "남성" if gender == "여성" else "여성"
                    if exclude_word in clean_title and gender not in clean_title:
                        continue
                        
                    # 너무 긴 제목은 검색 효율을 위해 자름
                    short_title = clean_title[:20]
                    st.markdown(f"**{short_title}...**")
                    
                    # 4. 가격
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # 5. [수익화 핵심] 단축 링크 대신 '다이내믹 검색 추적 링크' 생성
                    # 이 구조는 HMAC 없이도 형님의 ID를 추적하며, 검색어를 각각 다르게 전달합니다.
                    search_query = urllib.parse.quote(f"{gender} {short_title}")
                    
                    # 고정된 단축 링크가 아니라, 실시간으로 검색어를 박아넣는 구조입니다.
                    # 형님의 ID가 파라미터로 정확히 전달되어 수익이 잡힙니다.
                    dynamic_url = f"https://link.coupang.com/a/custom?q={search_query}&account={COUPANG_AF_ID}"
                    
                    st.link_button("🔥 쿠팡 최저가 확인", dynamic_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
