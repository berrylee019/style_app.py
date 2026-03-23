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
    
    # 형님의 정보 (수정 금지)
    COUPANG_AF_ID = "AF5326630"
    MY_COUPANG_LINK = "https://link.coupang.com/a/d9V87d"
    
except Exception as e:
    st.error("⚠️ Secrets 설정(API 키 등)을 다시 한번 확인해 주셔요!")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API (성별 필터링 강화) ---
def get_naver_products(gender, keyword):
    # 반대 성별 키워드는 아예 제외하도록 명령 (-키워드 활용)
    exclude_word = "남성" if gender == "여성" else "여성"
    # 예: "여성 오버핏 셔츠 -남성" -> 남성용은 검색 결과에서 제외됨
    refined_query = f"{gender} {keyword} -{exclude_word}"
    
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

# --- [함수] 키워드 추출 ---
def extract_shop_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[?(.*?)\]?$', text, re.MULTILINE)
    if match:
        keywords = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return keywords[0] if keywords else "트렌디 패션"
    return "트렌디 패션"

# --- UI ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 성별 맞춤 분석 & 수익형 쿠팡 매칭 시스템")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("분석할 성별 (필수)", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 (Gemini 역할 부여) ---
if uploaded_file:
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"베테랑 스타일리스트가 {gender} 패션을 분석 중..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                너는 15년 경력의 베테랑 패션 스타일리스트야.
                영상 속 인물의 '{gender}' 패션 스타일을 아주 전문적으로 분석해줘.
                
                [주의사항]
                1. 반드시 {gender} 의류 관점에서만 분석해.
                2. 중성적인 스타일이라도 {gender} 카테고리에서 구매 가능한 아이템 위주로 추천해.
                3. 마지막 줄에 반드시 아래 형식을 지켜:
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
        with st.spinner("맞춤 상품 찾는 중..."):
            # 검색 단계부터 성별을 강력하게 주입
            products = get_naver_products(gender, st.session_state.get('search_keyword', '패션'))
            if products:
                st.session_state['naver_products'] = products
                st.session_state['products_done'] = True
                st.rerun()
            else:
                st.warning("상품 정보를 가져오지 못했습니다.")

# --- [STEP 3] 최종 카드 (쿠팡 링크 정밀 수정) ---
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
                    
                    # [2중 필터] 제목에 반대 성별이 들어있으면 노출 안 함
                    exclude_word = "남성" if gender == "여성" else "여성"
                    if exclude_word in clean_title and gender not in clean_title:
                        continue

                    st.markdown(f"**{clean_title[:15]}...**")
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # --- [수익화 링크 최종 수술] ---
                    # 검색어 인코딩
                    search_keyword = f"{gender} {clean_title}"
                    encoded_search = urllib.parse.quote(search_keyword)
                    
                    # [가장 확실한 방법] 형님의 단축링크 뒤에 쿠팡 검색 파라미터를 붙이는 대신, 
                    # 쿠팡 파트너스에서 공식적으로 지원하는 '동적 검색 랜딩 URL' 형식을 사용합니다.
                    # 이 주소는 형님의 ID를 추적하면서 검색어 결과로 바로 보냅니다.
                    final_url = f"{MY_COUPANG_LINK}?subid=&q={encoded_search}"
                    
                    st.link_button("🔥 쿠팡 최저가 확인", final_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 이 서비스는 쿠팡 파트너스 활동을 통해 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
