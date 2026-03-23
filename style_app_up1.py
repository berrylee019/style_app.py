import streamlit as st
import google.generativeai as genai
import requests
import re
import urllib.parse

# 1. API 설정 (형님의 네이버 키 사용)
NAVER_ID = "CS3M6p8wqe7L4t1W4pbW"
NAVER_SECRET = "uh542B_0BS"
MY_REVENUE_LINK = "https://link.inpock.co.kr/shopping1" # 형님의 수익 창구

try:
    genai.configure(api_key=st.secrets["MY_API_KEY"])
except:
    st.error("⚠️ Streamlit Secrets에 'MY_API_KEY'를 설정해주세요.")

st.set_page_config(page_title="AI 스타일 가이드 PRO", page_icon="👗", layout="wide")

# --- [함수] 네이버 쇼핑 API (성별 격리 필터 강화) ---
def get_strictly_gender_item(gender, keyword):
    # 성별 섞임을 원천 차단하는 마이너스(-) 검색 전략
    exclude = "남성" if gender == "여성" else "여성"
    # 예: "여성 셋업 자켓 -남성 -공용 -남녀공용"
    refined_query = f"{gender} {keyword} -{exclude} -공용 -남녀공용"
    
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

# --- [함수] 4개 아이템 추출 ---
def extract_4_keywords(text):
    match = re.search(r'#\s*쇼핑\s*키워드\s*:\s*\[(.*?)\]', text, re.MULTILINE)
    if match:
        k_list = [k.strip().replace('[', '').replace(']', '') for k in match.group(1).split(',')]
        return k_list[:4]
    return ["상의", "하의", "신발", "가방"]

# --- UI 레이아웃 ---
st.title("👗 AI 스타일 가이드 PRO")
st.markdown(f"##### 형님, 성별은 '정확하게', 클릭은 '수익({MY_REVENUE_LINK})'으로!")

gender = st.radio("분석 성별 선택", ["여성", "남성"], horizontal=True)
uploaded_file = st.file_uploader("패션 스타일 영상 업로드", type=["mp4", "mov"])

if uploaded_file:
    if st.button("🚀 스타일 분석 및 수익 아이템 매칭"):
        with st.spinner(f"AI가 {gender} 스타일을 분석하고 있습니다..."):
            try:
                # 1. Gemini 분석 (성별 지침 강화)
                video_data = uploaded_file.read()
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""
                영상 속 스타일을 분석해서 패션 리포트를 작성해줘. 
                대상은 반드시 '{gender}'이야. 절대 반대 성별 아이템을 언급하지 마.
                마지막 줄에 반드시 이 형식을 지켜서 4개 아이템을 뽑아줘:
                # 쇼핑 키워드: [{gender} 상의, {gender} 하의, {gender} 신발, {gender} 액세서리]
                """
                response = model.generate_content([prompt, {"mime_type": "video/mp4", "data": video_data}])
                
                # 2. 키워드 추출 및 네이버 API 호출
                keywords = extract_4_keywords(response.text)
                final_products = []
                for kw in keywords:
                    prod = get_strictly_gender_item(gender, kw)
                    if prod: final_products.append(prod)

                # 3. 결과 출력
                st.divider()
                st.subheader("📊 AI 스타일 분석 결과")
                st.info(response.text)
                
                st.subheader(f"🛒 추천 {gender} 아이템 4선")
                if final_products:
                    cols = st.columns(len(final_products))
                    for i, item in enumerate(final_products):
                        with cols[i]:
                            with st.container(border=True):
                                title = item['title'].replace('<b>', '').replace('</b>', '')
                                st.image(item['image'], use_container_width=True)
                                st.markdown(f"**{title[:15]}...**")
                                st.markdown(f"**{int(item['lprice']):,}원**")
                                
                                # [핵심] 모든 버튼을 형님의 인포크링크로 연결
                                st.link_button("🔥 최저가 혜택받기", MY_REVENUE_LINK, use_container_width=True, type="primary")
                                st.caption("※ 클릭 시 인포크 전용 혜택 페이지로 이동합니다.")
                
                st.success(f"형님, 모든 상품 버튼이 인포크링크({MY_REVENUE_LINK})로 연결되었습니다!")

            except Exception as e:
                st.error(f"오류 발생: {e}")
