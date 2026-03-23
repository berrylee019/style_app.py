import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. 환경 설정 및 API 키 확인
try:
    # Gemini API 설정
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    
    # 네이버 API 설정
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
    
    # [수익화 설정] 형님의 쿠팡 파트너스 고유 ID 적용
    COUPANG_AF_ID = "AF5326630"
    
except Exception as e:
    st.error(f"⚠️ 설정 오류! .streamlit/secrets.toml에 MY_API_KEY, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET이 있는지 확인해 주셔요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="centered")

# --- [함수] 네이버 쇼핑 API 엔진 (상품 정보 수집 전용) ---
def get_naver_products(keyword):
    encoded_keyword = urllib.parse.quote(keyword)
    # 정확도를 위해 4개만 가져옵니다.
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
        else:
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
st.markdown("##### 당신의 스타일을 분석하고, 가장 잘 어울리는 아이템을 찾아드립니다.")

# 세션 상태 초기화 (에러 방지용)
if 'analysis_done' not in st.session_state:
    st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state:
    st.session_state['products_done'] = False

gender = st.radio("분석할 성별을 선택하세요", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 스타일링 영상 업로드 (5~10초)", type=["mp4", "mov"])

# --- [STEP 1] 분석 로직 (먹통 해결 버전) ---
if uploaded_file:
    # 1단계 버튼
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일 영상을 정밀하게 분석하고 있습니다..."):
            try:
                # 영상 바이트 데이터 읽기
                video_data = uploaded_file.read()
                
                # Gemini 1.5 Flash 모델 사용 (비전 분석 최적화)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 성별 맞춤 프롬프트 구성
                prompt = f"""
                영상 속 인물의 패션 스타일을 보고 전문가의 시선으로 리포트를 작성해줘.
                사용자의 성별은 '{gender}'이야. 반드시 {gender} 패션 스타일 위주로 분석해줘.
                리포트 마지막 줄에는 반드시 아래 형식을 포함해야 해:
                # 쇼핑 키워드: [{gender} 스타일 키워드]
                """
                
                # AI 호출
                response = model.generate_content([
                    prompt,
                    {"mime_type": "video/mp4", "data": video_data}
                ])
                
                # 분석 결과 저장
                st.session_state['analysis_result'] = response.text
                st.session_state['search_keyword'] = extract_shop_keywords(response.text)
                st.session_state['analysis_done'] = True
                st.rerun() # 화면 즉시 갱신
                
            except Exception as e:
                st.error(f"⚠️ 분석 중 오류가 발생했습니다: {e}")

# --- [STEP 2] 리포트 출력 및 상품 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    # 2단계 버튼
    if st.button("2단계: 추천 상품 실시간 매칭", key="matching_step_btn"):
        # 분석된 키워드에 성별을 한 번 더 붙여서 '성별 불일치' 원천 차단
        base_keyword = st.session_state.get('search_keyword', '패션')
        target_keyword = f"{gender} {base_keyword}"
        
        with st.spinner(f"'{target_keyword}' 관련 최적의 상품을 찾는 중..."):
            products = get_naver_products(target_keyword)
            
            if products:
                st.session_state['naver_products'] = products
                st.session_state['products_done'] = True
                st.success("매칭 성공! 하단에서 추천 아이템을 확인하세요.")
                st.rerun()
            else:
                st.warning("네이버 쇼핑에서 상품 정보를 가져오지 못했습니다.")

# --- [STEP 3] 최종 수익형 상품 카드 출력 (하이브리드 모델) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 스타일 추천 아이템")

    products = st.session_state.get('naver_products', [])
    
    if products:
        cols = st.columns(len(products))
        for i, item in enumerate(products):
            with cols[i]:
                with st.container(border=True):
                    # 1. 상품 이미지 (네이버 API 데이터)
                    st.image(item['image'], use_container_width=True)
                    
                    # 2. 상품 제목 정화 (<b> 태그 제거)
                    clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                    
                    # 3. 여성 선택 시 남성 전용 상품 필터링
                    if gender == "여성" and ("남성" in clean_title) and "여성" not in clean_title:
                        st.caption("공용/남성 상품 제외")
                        continue
                        
                    st.markdown(f"**{clean_title[:15]}...**")
                    
                    # 4. 가격 정보
                    price = int(item['lprice']) if item['lprice'].isdigit() else 0
                    st.markdown(f"**{price:,}원**")
                    
                    # 5. [수익화 핵심] 쿠팡 파트너스 검색 링크로 치환
                    # 네이버에서 찾은 상품명을 쿠팡 검색 페이지로 연결하며 형님의 ID를 심습니다.
                    search_query = urllib.parse.quote(f"{gender} {clean_title}")
                    affiliate_url = f"https://link.coupang.com/a/custom?q={search_query}&account={COUPANG_AF_ID}"
                    
                    # 클릭 시 수익이 발생하는 버튼
                    st.link_button("🔥 쿠팡 최저가 확인", affiliate_url, use_container_width=True, type="primary")
    
    # [법적 문구 필수] 수익화를 위해 이 문구가 반드시 노출되어야 합니다.
    st.markdown("---")
    st.caption(f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받을 수 있습니다. (ID: {COUPANG_AF_ID})")
