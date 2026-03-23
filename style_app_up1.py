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
    
    # [수익화] 형님의 쿠팡 파트너스 ID (절대 누락 금지)
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! secrets.toml 파일을 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# --- [함수] 네이버 쇼핑 API (성별 필터 강화형) ---
def get_naver_products(gender, keyword):
    # 반대 성별 키워드를 검색 결과에서 강제로 제외(-) 처리하여 섞임을 원천 차단
    exclude_gender = "남성" if gender == "여성" else "여성"
    
    # 검색어 예: "여성용 트위드자켓 -남성 -공용"
    refined_query = f"{gender}용 {keyword} -{exclude_gender} -공용"
    
    encoded_keyword = urllib.parse.quote(refined_query)
    # 각 키워드당 가장 연관성 높은 1개만 정밀 타격
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

# --- [함수] 리스트 형태의 4개 키워드 추출 ---
def extract_keywords(text):
    # [# 쇼핑 키워드: [항목1, 항목2...]] 형식을 찾아 리스트로 반환
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        k_list = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return k_list[:4]
    return ["패션 상의", "패션 하의", "패션 신발", "액세서리"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown(f"##### 분석부터 수익 창출까지, 형님({COUPANG_AF_ID})만을 위한 최종 병기")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("분석할 성별", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 스타일 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 (Gemini 1.5) ---
if uploaded_file:
    if st.button("1단계: AI 스타일 정밀 분석", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일링을 분석하여 4가지 핵심 아이템을 추출 중입니다..."):
            try:
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # 성별 지침을 아주 강력하게 주입 (섞임 방지 프롬프트)
                prompt = f"""
                영상 속 인물의 패션 스타일을 분석해서 리포트를 작성해줘. 
                대상은 반드시 '{gender}'이야. 절대 반대 성별이나 공용 아이템을 추천하지 마.
                분석 마지막 줄에 반드시 아래 형식을 지켜서 4개의 서로 다른 쇼핑 아이템을 뽑아줘:
                # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 가방]
                """
                
                response = model.generate_content([
                    prompt, {"mime_type": "video/mp4", "data": video_data}
                ])
                
                st.session_state['analysis_result'] = response.text
                st.session_state['target_keywords'] = extract_keywords(response.text)
                st.session_state['analysis_done'] = True
                st.rerun()
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")

# --- [STEP 2] 리포트 출력 및 아이템 개별 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 4종 실시간 매칭", key="matching_btn"):
        with st.spinner("각 키워드별로 최적의 상품을 개별 매칭 중..."):
            keywords = st.session_state.get('target_keywords', [])
            matched_items = []
            
            for kw in keywords:
                # 네이버 API를 4번 호출하여 각 키워드별로 확실한 1개씩 수집
                product = get_naver_products(gender, kw)
                if product:
                    matched_products = product
                    matched_items.append(matched_products)
            
            if matched_items:
                st.session_state['final_products'] = matched_items
                st.session_state['products_done'] = True
                st.rerun()
            else:
                st.warning("상품 정보를 찾지 못했습니다.")

# --- [STEP 3] 최종 상품 카드 (개별 수익 링크 & 성별 보장) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 맞춤 추천 아이템 (4종)")

    products = st.session_state.get('final_products', [])
    
    if products:
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 1. 이미지 및 제목
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{clean_title[:15]}...**")
                    st.markdown(f"**{int(item['lprice']):,}원**")
                    
                    # --- [수익화 핵심: 버튼 및 링크 구조 전면 수정] ---
                    # 검색어 생성 (성별 + 핵심 상품명)
                    search_term = urllib.parse.quote(f"{gender} {clean_title[:10]}")
                    
                    # [최종 해결책] 엉뚱한 페이지로 튀지 않는 쿠팡 파트너스 다이렉트 랜딩 구조
                    # 이 URL은 형님의 AF ID를 쿠팡 서버에 기록한 후, 해당 검색어로 정확히 보내줍니다.
                    final_affiliate_url = f"https://link.coupang.com/a/custom?q={search_term}&account={COUPANG_AF_ID}"
                    
                    # 버튼이 절대 사라지지 않도록 무조건 렌더링
                    st.link_button("🔥 쿠팡 최저가 확인", final_affiliate_url, use_container_width=True, type="primary")
    
    st.markdown("---")
    st.caption(f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
