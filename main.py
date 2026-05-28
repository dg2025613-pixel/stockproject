import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time # 💡 시간 지연(sleep)을 사용하기 위해 추가했어요!

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="글로벌 주식 분석 대시보드 📊",
    page_icon="📈",
    layout="wide"
)

# CSS 스타일링
st.markdown("""
    <style>
    .title-text {
        text-align: center;
        color: #2e4053;
        font-weight: bold;
        padding: 20px;
    }
    .info-box {
        background-color: #e8f8f5;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1abc9c;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

STOCKS = {
    "🇺🇸 애플 (AAPL)": "AAPL",
    "🇺🇸 마이크로소프트 (MSFT)": "MSFT",
    "🇺🇸 테슬라 (TSLA)": "TSLA",
    "🇺🇸 엔비디아 (NVDA)": "NVDA",
    "🇰🇷 삼성전자": "005930.KS",
    "🇰🇷 SK하이닉스": "000660.KS",
    "🇰🇷 현대자동차": "005380.KS",
    "🇰🇷 카카오": "035720.KS"
}

# 3. 데이터 불러오기 함수 (Rate Limit 방어 로직 추가!)
# ttl=3600을 추가하면 1시간(3600초) 동안은 야후 서버에 다시 요청하지 않고 저장된 데이터를 써요!
@st.cache_data(ttl=3600)
def load_stock_data(tickers, start_date, end_date):
    df = pd.DataFrame()
    for name, ticker in tickers.items():
        try: # 💡 예외 처리 시작: 에러가 나도 앱이 멈추지 않게 보호합니다.
            # yfinance를 통해 데이터 다운로드
            stock_obj = yf.Ticker(ticker)
            hist = stock_obj.history(start=start_date, end=end_date)
            
            if not hist.empty:
                df[name] = hist['Close']
            
            # 💡 핵심 방어 로직: 야후 서버가 봇으로 오해하지 않도록 1초씩 쉬어줍니다.
            time.sleep(1)
            
        except Exception as e:
            # 특정 종목에서 에러가 나면 경고창만 띄우고 다음 종목으로 넘어갑니다.
            st.warning(f"⚠️ '{name}' 데이터를 가져오는 중 문제가 발생했습니다. (야후 파이낸스 접속 제한 등)")
            
    return df

# --- 메인 화면 ---
st.markdown('<h1 class="title-text">📈 글로벌 주요 주식 수익률 분석기</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
    <b>💡 학습 포인트:</b> 파이썬의 <code>try-except</code> 구문과 <code>time.sleep()</code>을 활용해 서버 차단(Rate Limit) 오류를 방어하는 방법을 배웁니다!<br>
    클라우드 환경에서는 여러 프로그램이 동시에 외부 데이터를 요청하므로, 항상 예외 상황을 고려해서 코드를 짜야 해요.
</div>
""", unsafe_allow_html=True)

# --- 사이드바 (설정 영역) ---
with st.sidebar:
    st.header("⚙️ 분석 설정")
    
    today = datetime.today()
    one_year_ago = today - timedelta(days=365)
    
    start_date = st.date_input("📅 시작일", one_year_ago)
    end_date = st.date_input("📅 종료일", today)
    
    selected_stocks = st.multiselect(
        "🔍 비교할 기업을 선택하세요",
        options=list(STOCKS.keys()),
        default=["🇺🇸 애플 (AAPL)", "🇰🇷 삼성전자"]
    )

# --- 데이터 처리 및 화면 출력 ---
if start_date > end_date:
    st.error("🚨 오류: 시작일이 종료일보다 늦을 수 없습니다. 날짜를 다시 설정해주세요!")
elif not selected_stocks:
    st.warning("👈 왼쪽 사이드바에서 분석할 기업을 1개 이상 선택해주세요!")
else:
    with st.spinner("로딩 중... 봇 차단을 막기 위해 천천히 데이터를 불러오고 있습니다 🔄"):
        selected_tickers = {name: STOCKS[name] for name in selected_stocks}
        
        raw_df = load_stock_data(selected_tickers, start_date, end_date)
        
        if raw_df.empty:
            st.error("🚨 선택한 기간의 데이터를 모두 불러오지 못했습니다. 야후 서버에서 스트림릿 클라우드의 접속을 일시 차단했을 수 있으니 몇 분 후 다시 시도해주세요.")
        else:
            return_df = ((raw_df / raw_df.iloc[0]) - 1) * 100
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 누적 수익률 비교 차트 (%)")
                fig = px.line(
                    return_df, 
                    labels={"value": "수익률 (%)", "index": "날짜", "variable": "기업명"},
                    template="plotly_white"
                )
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("💰 기간 내 최종 수익률")
                final_returns = return_df.iloc[-1].sort_values(ascending=False)
                
                for stock_name, current_return in final_returns.items():
                    if current_return > 0:
                        delta_color = "normal"
                    else:
                        delta_color = "inverse"
                        
                    st.metric(
                        label=stock_name, 
                        value=f"{raw_df[stock_name].iloc[-1]:,.0f}", 
                        delta=f"{current_return:.2f}%", 
                        delta_color=delta_color
                    )
                    
            st.markdown("---")
            with st.expander("📝 원본 주가 데이터 (DataFrame) 보기"):
                st.dataframe(raw_df)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>
    당곡고등학교 AI 도우미 🤖 | 본 데이터는 학습 및 탐구 목적으로 제공됩니다.
</div>
""", unsafe_allow_html=True)
