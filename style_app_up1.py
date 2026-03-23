import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. API 및 환경 설정
try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
    NAVER_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
except Exception as e:
    st.error(f"⚠️ 설정 오류! .streamlit/secrets.toml 확인: {e}")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# --- [함수] 네이버 쇼핑 API (성별 고립 검색) ---
def get_naver_item(gender, keyword):
    # 반대 성별 키워드를 검색어에서 제거(-)하여 성별 섞임을 원천 차단
    exclude = "남성" if gender == "여성" else "여성"
    # 예: "여성용 오버핏 자켓 -남성 -공용"
    refined_query = f"{gender}용 {keyword} -{exclude} -공용"
    
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

# --- [함수] 4개의 개별 키워드 정밀 추출 ---
def extract_keywords_list(text):
    # Gemini가 출력한 리포트에서 # 쇼핑 키워드: [A, B, C, D] 추출
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        raw = match.group(1).split(',')
        return [k.strip().replace('[', '').replace(']', '') for k in raw][:4]
    return ["트렌디 상의", "슬림핏 하의", "데일리 슈즈", "패션 소품"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown("##### 형님, 네이버 쇼핑 엔진으로 성별은 정확하게, 수익화는 안전하게 잡았습니다.")

if 'analysis_done' not in st.session_state: st.session_state['analysis_done'] = False
if 'products_done' not in st.session_state: st.session_state['products_done'] = False

gender = st.radio("성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 영상 업로드", type=["mp4", "mov"])

# --- [STEP 1] 영상 분석 ---
if uploaded_file:
    if st.button("1단계: AI 스타일 분석하기", key="analysis_btn"):
        with st.spinner(f"AI가 {gender} 스타일링을 정밀 분석 중입니다..."):
            try:
                video_data = uploaded_file.read()
                # 최신 Gemini 1.5 Flash 사용 (영상 분석 최적화)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                영상 속 인물의 패션 스타일을 분석해서 전문가 리포트를 작성해줘.
                사용자의 성별은 반드시 '{gender}'이야. 절대 반대 성별 상품을 추천하면 안 돼.
                마지막 줄에 반드시 아래 형식을 지켜서 서로 다른 4가지 쇼핑 아이템을 뽑아줘:
                # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 액세서리]
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

# --- [STEP 2] 아이템 매칭 ---
if st.session_state.get('analysis_done'):
    st.divider()
    st.subheader("📊 AI 스타일 리포트")
    st.info(st.session_state.analysis_result)
    
    if st.button("2단계: 추천 상품 4종 매칭", key="matching_btn"):
        with st.spinner("네이버 쇼핑에서 아이템별 최저가를 찾는 중..."):
            keywords = st.session_state.get('target_keywords', [])
            final_items = []
            
            for kw in keywords:
                res = get_naver_item(gender, kw)
                if res: final_items.append(res)
            
            if final_items:
                st.session_state['matched_products'] = final_items
                st.session_state['products_done'] = True
                st.rerun()

# --- [STEP 3] 최종 결과 전시 (수익화 연결) ---
if st.session_state.get('products_done'):
    st.divider()
    st.subheader(f"🛒 {gender} 맞춤 실시간 추천 리스트")
    
    products = st.session_state.get('matched_products', [])
    cols = st.columns(len(products))
    
    for i, item in enumerate(products):
        with cols[i]:
            with st.container(border=True):
                # 이미지 및 정보
                st.image(item['image'], use_container_width=True)
                clean_title = item['title'].replace('<b>', '').replace('</b>', '')
                st.markdown(f"**{clean_title[:15]}...**")
                st.markdown(f"**{int(item['lprice']):,}원**")
                
                # --- [수익화 전략 포인트] ---
                # 네이버 쇼핑은 링크 자체에 형님의 제휴 마케팅 코드를 심는 방식이 필요합니다.
                # 현재는 기본 네이버 최저가 링크로 연결되지만, 
                # 나중에 네이버 애드포스트 코드가 나오면 URL 뒤에 ?tracking_id=형님ID 식으로 붙이면 됩니다.
                naver_url = item['link']
                
                st.link_button("🎁 최저가 구매하기", naver_url, use_container_width=True, type="primary")

    st.markdown("---")
    st.caption(f"※ 본 추천은 네이버 쇼핑 API를 통한 {gender}용 실시간 데이터입니다.")
