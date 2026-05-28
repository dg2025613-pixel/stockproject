import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="삼성전자 집중 분석 🔎",
    page_icon="📱",
    layout="wide"
)

# CSS 스타일링
st.markdown("""
    <style>
    .title-text {
        text-align: center;
        color: #0b3d91;
        font-weight: bold;
        padding: 20px;
        background-color: #f0f4f8;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #e8f8f5;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1abc9c;
        margin-bottom: 20px;
    }
    .stat-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 데이터 불러오기 함수 (삼성전자 전용)
@st.cache_data(ttl=3600)
def load_samsung_data(start_date, end_date):
    ticker = "005930.KS"  # 삼성전자의 야후 파이낸스 티커
    samsung = yf.Ticker(ticker)
    
    # 주가 데이터 가져오기
    df = samsung.history(start=start_date, end=end_date)
    
    # 재무 정보 가져오기 (오류 발생 시 빈 딕셔너리 반환)
    try:
        info = samsung.info
    except:
        info = {}
        
    return df, info

# --- 메인 화면 시작 ---
st.markdown('<h1 class="title-text">🔎 삼성전자(005930) 집중 분석 대시보드</h1>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <b>💡 학습 포인트:</b><br>
    1. <b>캔들 차트(Candlestick):</b> 하루 동안의 시가, 종가, 고가, 저가를 한눈에 보여줍니다.<br>
    2. <b>이동평균선(Moving Average):</b> <code>pandas</code>의 <code>rolling().mean()</code> 함수를 사용해 계산된 20일, 60일, 120일 평균 주가 선을 통해 추세를 파악합니다.<br>
    3. <b>데이터 시각화:</b> <code>plotly.subplots</code>를 활용해 위에는 주가, 아래에는 거래량을 동시에 시각화합니다.
</div>
""", unsafe_allow_html=True)

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 분석 기간 설정")
    
    today = datetime.today()
    # 기본 분석 기간을 2년으로 설정
    two_years_ago = today - timedelta(days=365 * 2)
    
    start_date = st.date_input("📅 시작일", two_years_ago)
    end_date = st.date_input("📅 종료일", today)
    
    st.markdown("---")
    st.info("💡 시작일과 종료일을 변경하여 특정 사건이 있었던 시기의 주가 흐름을 분석해보세요!")

# --- 데이터 분석 및 화면 출력 ---
if start_date > end_date:
    st.error("🚨 오류: 시작일이 종료일보다 늦을 수 없습니다.")
else:
    with st.spinner("삼성전자 데이터를 정밀 분석 중입니다... 🔄"):
        df, info = load_samsung_data(start_date, end_date)
        
        if df.empty:
            st.error("🚨 데이터를 불러오지 못했습니다. 주말/공휴일 등 거래가 없는 기간만 선택했는지 확인하거나, 잠시 후 다시 시도해주세요.")
        else:
            # 1. 데이터 전처리: 이동평균선 계산 (20일, 60일, 120일)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            
            # --- 섹션 1: 기업 요약 정보 ---
            st.markdown("### 🏢 기업 현재 요약")
            col1, col2, col3, col4 = st.columns(4)
            
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            market_cap = info.get('marketCap', '데이터 없음')
            if isinstance(market_cap, (int, float)):
                market_cap = f"{market_cap / 1000000000000:,.0f}조 원"
                
            per = info.get('trailingPE', '데이터 없음')
            if isinstance(per, (int, float)):
                per = f"{per:.2f}배"
                
            div_yield = info.get('dividendYield', '데이터 없음')
            if isinstance(div_yield, (int, float)):
                div_yield = f"{div_yield * 100:.2f}%"

            with col1:
                st.metric(label="마지막 거래일 주가", value=f"{current_price:,.0f}원", delta=f"{price_change:.2f}% (전일 대비)")
            with col2:
                st.metric(label="시가총액", value=market_cap)
            with col3:
                st.metric(label="PER (주가수익비율)", value=per)
            with col4:
                st.metric(label="배당 수익률", value=div_yield)
                
            st.markdown("---")
            
            # --- 섹션 2: 캔들 차트 및 이동평균선, 거래량 ---
            st.markdown("### 📉 정밀 차트 분석 (캔들 차트 & 거래량)")
            
            # 2개의 차트를 위아래로 붙이기 (비율 7:3)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # 1) 위쪽 차트: 캔들 차트 추가
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], 
                low=df['Low'], close=df['Close'], name='캔들 차트',
                increasing_line_color='red', decreasing_line_color='blue' # 한국은 상승이 빨간색!
            ), row=1, col=1)
            
            # 1) 위쪽 차트: 이동평균선 추가
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name='20일 선 (MA20)'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='green', width=1.5), name='60일 선 (MA60)'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA120'], line=dict(color='purple', width=1.5), name='120일 선 (MA120)'), row=1, col=1)
            
            # 2) 아래쪽 차트: 거래량 바 차트 추가
            # 주가가 오른 날은 빨간색, 내린 날은 파란색으로 거래량 표시
            colors = ['red' if close >= open else 'blue' for close, open in zip(df['Close'], df['Open'])]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='거래량'), row=2, col=1)
            
            # 차트 레이아웃 설정
            fig.update_layout(
                title='삼성전자 주가 및 거래량 추이',
                yaxis_title='주가 (원)',
                yaxis2_title='거래량',
                xaxis_rangeslider_visible=False, # 캔들차트 기본 슬라이더 숨기기
                template="plotly_white",
                height=700,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

# 하단 꼬리말
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; font-size: 0.9em;'>
    당곡고등학교 AI 도우미 🤖 | 본 대시보드는 정보 교과 및 경제 융합 탐구를 위해 제작되었습니다.
</div>
""", unsafe_allow_html=True)
