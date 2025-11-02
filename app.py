import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
import json
import os
import random
import time

# config import를 try-except로 처리
try:
    from config import COLORS, REGIONS, STAMP_BENEFITS, SMS_CONFIG, SEAT_LAYOUT
except ImportError as e:
    st.error(f"❌ config.py 파일을 불러올 수 없습니다: {e}")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="티켓츠 QR 발권",
    page_icon="🎫",
    layout="wide"
)

# CSS 스타일 (TCATS 디자인)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    
    * {{
        font-family: 'Noto Sans KR', sans-serif;
    }}
    
    .main-header {{
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, {COLORS['primary']} 0%, #C41E3A 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .main-header h1 {{
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }}
    
    .main-header p {{
        font-size: 1.1rem;
        opacity: 0.9;
    }}
    
    .step-card {{
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    
    .verification-box {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    .verification-code {{
        font-size: 3rem;
        font-weight: bold;
        letter-spacing: 1rem;
        margin: 1rem 0;
        color: #FFD700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    
    .timer {{
        font-size: 1.5rem;
        color: #FFD700;
        font-weight: bold;
    }}
    
    .ticket-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    .seat-badge {{
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.9rem;
    }}
    
    .success-box {{
        background: #d4edda;
        border-left: 5px solid {COLORS['success']};
        padding: 1.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }}
    
    .info-box {{
        background: #d1ecf1;
        border-left: 5px solid {COLORS['secondary']};
        padding: 1.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }}
    
    .warning-box {{
        background: #fff3cd;
        border-left: 5px solid {COLORS['warning']};
        padding: 1.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }}
    
    .stButton>button {{
        width: 100%;
        background: {COLORS['primary']};
        color: white;
        font-weight: bold;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        border: none;
        font-size: 1.1rem;
        transition: all 0.3s;
    }}
    
    .stButton>button:hover {{
        background: #C41E3A;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'selected_performance' not in st.session_state:
    st.session_state.selected_performance = None
if 'verified_user' not in st.session_state:
    st.session_state.verified_user = None
if 'tickets' not in st.session_state:
    st.session_state.tickets = []
if 'is_companion' not in st.session_state:
    st.session_state.is_companion = False
if 'companion_ticket_data' not in st.session_state:
    st.session_state.companion_ticket_data = None

# SMS 인증 관련 세션 상태
if 'verification_code' not in st.session_state:
    st.session_state.verification_code = None
if 'verification_time' not in st.session_state:
    st.session_state.verification_time = None
if 'verification_attempts' not in st.session_state:
    st.session_state.verification_attempts = 0
if 'is_verified' not in st.session_state:
    st.session_state.is_verified = False

# 좌석 선택 관련 세션 상태
if 'selected_seats' not in st.session_state:
    st.session_state.selected_seats = []

# 데이터 폴더 생성
os.makedirs('data', exist_ok=True)

# ==================== 함수 정의 ====================

def load_reservations():
    """예매자 명부 불러오기"""
    try:
        df = pd.read_excel('data/reservations.xlsx')
        return df
    except FileNotFoundError:
        st.error("❌ 예매자 명부 파일이 없습니다.")
        return None
    except Exception as e:
        st.error(f"❌ 파일 읽기 오류: {e}")
        return None

def search_reservation(df, name, phone_last4, performance, date, session):
    """예매 정보 검색 (여러 장 지원)"""
    try:
        result = df[
            (df['이름'] == name) & 
            (df['전화번호'].astype(str).str.endswith(phone_last4)) &
            (df['공연명'] == performance) &
            (df['공연일시'] == date) &
            (df['회차'] == session)
        ]
        return result
    except Exception as e:
        st.error(f"❌ 검색 오류: {e}")
        return pd.DataFrame()

def generate_verification_code():
    """인증번호 생성 (4자리)"""
    return ''.join([str(random.randint(0, 9)) for _ in range(SMS_CONFIG['code_length'])])

def send_sms_verification(phone_number, code):
    """SMS 발송 (모의)"""
    st.session_state.verification_code = code
    st.session_state.verification_time = datetime.now()
    st.session_state.verification_attempts = 0
    return True

def check_verification_expired():
    """인증번호 만료 여부 확인"""
    if st.session_state.verification_time is None:
        return True
    
    elapsed = (datetime.now() - st.session_state.verification_time).total_seconds()
    return elapsed > (SMS_CONFIG['valid_minutes'] * 60)

def get_remaining_time():
    """남은 시간 계산 (초)"""
    if st.session_state.verification_time is None:
        return 0
    
    elapsed = (datetime.now() - st.session_state.verification_time).total_seconds()
    remaining = (SMS_CONFIG['valid_minutes'] * 60) - elapsed
    return max(0, int(remaining))

def get_occupied_seats(performance, date, session):
    """이미 예약된 좌석 목록 가져오기"""
    try:
        df = load_reservations()
        if df is None:
            return []
        
        occupied = df[
            (df['공연명'] == performance) &
            (df['공연일시'] == date) &
            (df['회차'] == session) &
            (df['좌석번호'].notna()) &
            (df['좌석번호'] != '')
        ]['좌석번호'].tolist()
        
        return occupied
    except Exception as e:
        st.warning(f"⚠️ 좌석 조회 중 오류: {e}")
        return []

def get_available_seats(performance):
    """선택 가능한 좌석 목록 생성"""
    try:
        # 공연명 확인
        if not performance:
            st.error("❌ 공연명이 지정되지 않았습니다.")
            return []
        
        # SEAT_LAYOUT 확인
        if performance not in SEAT_LAYOUT:
            st.error(f"❌ '{performance}' 공연의 좌석 정보가 없습니다.")
            st.info(f"🔍 사용 가능한 공연: {', '.join(SEAT_LAYOUT.keys())}")
            return []
        
        available_seats = []
        layout = SEAT_LAYOUT[performance]
        
        # sections 키 확인
        if 'sections' not in layout:
            st.error(f"❌ '{performance}' 공연의 좌석 구성 정보가 잘못되었습니다.")
            return []
        
        sections = layout['sections']
        
        # 각 섹션 처리
        for section in sections:
            try:
                section_name = section.get('name', '알 수 없음')
                rows = section.get('rows', [])
                seats_per_row = section.get('seats_per_row', 0)
                price = section.get('price', 0)
                color = section.get('color', '#CCCCCC')
                
                for row in rows:
                    for num in range(1, seats_per_row + 1):
                        seat_id = f"{row}-{num:02d}"
                        available_seats.append({
                            'seat_id': seat_id,
                            'section': section_name,
                            'price': price,
                            'color': color
                        })
            except Exception as e:
                st.warning(f"⚠️ 섹션 처리 중 오류: {e}")
                continue
        
        return available_seats
        
    except Exception as e:
        st.error(f"❌ 좌석 목록 생성 오류: {e}")
        return []

def generate_qr_code(ticket_data):
    """QR 코드 생성"""
    try:
        qr_data = json.dumps(ticket_data, ensure_ascii=False)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        byte_im = buf.getvalue()
        
        return byte_im
    except Exception as e:
        st.error(f"❌ QR 코드 생성 오류: {e}")
        return None

def save_companion_info(companion_data):
    """동반자 정보 저장"""
    try:
        file_path = 'data/companion_info.csv'
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
        else:
            df = pd.DataFrame()
        
        new_row = pd.DataFrame([companion_data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file_path, index=False)
        return True
    except Exception as e:
        st.error(f"❌ 동반자 정보 저장 오류: {e}")
        return False

# ==================== 헤더 ====================

st.markdown(f'''
<div class="main-header">
    <h1>🎭 티켓츠 QR 발권 서비스</h1>
    <p>RIGHT TIME, RIGHT PERSON - Joyful Recommendation</p>
</div>
''', unsafe_allow_html=True)

# ==================== 사이드바 ====================

with st.sidebar:
    st.header("📌 메뉴")
    
    if st.button("🔄 처음으로", use_container_width=True):
        st.session_state.step = 1
        st.session_state.selected_performance = None
        st.session_state.verified_user = None
        st.session_state.tickets = []
        st.session_state.is_companion = False
        st.session_state.companion_ticket_data = None
        st.session_state.verification_code = None
        st.session_state.verification_time = None
        st.session_state.verification_attempts = 0
        st.session_state.is_verified = False
        st.session_state.selected_seats = []
        st.rerun()
    
    st.markdown("---")
    st.caption("현재 단계:")
    if st.session_state.is_companion:
        st.info("👥 동반자 정보 등록")
    elif st.session_state.step == 1:
        st.info("1️⃣ 공연 선택")
    elif st.session_state.step == 2:
        st.info("2️⃣ 본인 확인")
    elif st.session_state.step == 2.5:
        st.info("📱 SMS 인증")
    elif st.session_state.step == 2.7:
        st.info("🪑 좌석 선택")
    elif st.session_state.step == 3:
        st.info("3️⃣ QR 발권")

# ==================== URL 파라미터로 동반자 모드 체크 ====================

query_params = st.query_params
if 'ticket' in query_params and not st.session_state.is_companion:
    try:
        ticket_json = query_params['ticket']
        st.session_state.companion_ticket_data = json.loads(ticket_json)
        st.session_state.is_companion = True
        st.rerun()
    except:
        pass

# ==================== 동반자 정보 등록 화면 ====================

if st.session_state.is_companion:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("👥 동반자 정보 등록")
    
    ticket_data = st.session_state.companion_ticket_data
    
    st.markdown(f"""
    <div class="info-box">
        <h4>📋 티켓 정보</h4>
        <p><strong>공연:</strong> {ticket_data.get('공연명', 'N/A')}</p>
        <p><strong>일시:</strong> {ticket_data.get('공연일시', 'N/A')} {ticket_data.get('회차', 'N/A')}</p>
        <p><strong>좌석:</strong> {ticket_data.get('좌석번호', '비지정석')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("### 🎁 동반자 정보를 등록하고 지역 할인 혜택을 받으세요!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        comp_name = st.text_input("이름*", placeholder="홍길동")
        comp_phone = st.text_input("전화번호*", placeholder="010-1234-5678")
    
    with col2:
        comp_gender = st.selectbox("성별*", ["선택", "남성", "여성", "기타"])
        comp_region = st.selectbox("거주지역 (읍면동)*", ["선택"] + REGIONS)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("✅ 등록하고 혜택 받기", type="primary", use_container_width=True):
        if not comp_name or not comp_phone or comp_gender == "선택" or comp_region == "선택":
            st.warning("⚠️ 모든 정보를 입력해주세요.")
        else:
            companion_data = {
                "등록일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "예매번호": ticket_data.get('예매번호', 'N/A'),
                "공연명": ticket_data.get('공연명', 'N/A'),
                "좌석번호": ticket_data.get('좌석번호', '비지정석'),
                "이름": comp_name,
                "전화번호": comp_phone,
                "성별": comp_gender,
                "거주지역": comp_region
            }
            
            if save_companion_info(companion_data):
                st.session_state.step = 4
                st.rerun()

# ==================== Step 1: 공연 선택 ====================
elif st.session_state.step == 1:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("1️⃣ 공연 정보 선택")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        performance = st.selectbox(
            "🎭 공연명",
            ["뮤지컬 오페라의 유령", "콘서트 BTS", "연극 햄릿"]
        )
    
    with col2:
        date = st.selectbox(
            "📅 공연일",
            ["2024-11-15", "2024-11-16", "2024-11-17", "2024-11-20", "2024-11-25"]
        )
    
    with col3:
        session = st.selectbox(
            "🕐 회차",
            ["14:00", "18:00", "19:00"]
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("다음 단계 →", type="primary", use_container_width=True):
        st.session_state.selected_performance = {
            "공연명": performance,
            "공연일시": date,
            "회차": session
        }
        st.session_state.step = 2
        st.rerun()

# ==================== Step 2: 본인 확인 ====================
elif st.session_state.step == 2:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("2️⃣ 예매자 본인 확인")
    
    perf = st.session_state.selected_performance
    st.info(f"🎭 {perf['공연명']} | 📅 {perf['공연일시']} | 🕐 {perf['회차']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("이름", placeholder="홍길동")
    
    with col2:
        phone_last4 = st.text_input("전화번호 마지막 4자리", placeholder="1234", max_chars=4)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col_back, col_search = st.columns([1, 2])
    
    with col_back:
        if st.button("← 이전", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    
    with col_search:
        if st.button("🔍 예매 내역 조회", type="primary", use_container_width=True):
            if not name or not phone_last4 or len(phone_last4) != 4:
                st.warning("⚠️ 이름과 전화번호 마지막 4자리를 정확히 입력해주세요.")
            else:
                df = load_reservations()
                if df is not None:
                    result = search_reservation(
                        df, name, phone_last4,
                        perf['공연명'], perf['공연일시'], perf['회차']
                    )
                    
                    if len(result) > 0:
                        st.session_state.verified_user = result
                        st.session_state.step = 2.5
                        st.rerun()
                    else:
                        st.error("❌ 예매 내역을 찾을 수 없습니다.")

# ==================== Step 2.5: SMS 인증 ====================
elif st.session_state.step == 2.5:
    user_data = st.session_state.verified_user
    phone_number = user_data.iloc[0]['전화번호']
    
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("📱 SMS 본인 인증")
    
    st.info(f"🎭 {user_data.iloc[0]['공연명']} | 👤 {user_data.iloc[0]['이름']}님")
    
    # 인증번호 발송
    if st.session_state.verification_code is None:
        code = generate_verification_code()
        send_sms_verification(phone_number, code)
    
    # 인증번호 만료 체크
    if check_verification_expired():
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("⏰ 인증번호가 만료되었습니다. 재발송 버튼을 눌러주세요.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🔄 인증번호 재발송", use_container_width=True):
            code = generate_verification_code()
            send_sms_verification(phone_number, code)
            st.rerun()
    else:
        # 인증번호 표시 (모의 SMS)
        st.markdown(f"""
        <div class="verification-box">
            <h3>📱 인증번호가 발송되었습니다</h3>
            <p>{phone_number}로 인증번호를 발송했습니다.</p>
            <p style="font-size: 0.9rem; opacity: 0.8;">(실제 서비스에서는 문자로 발송됩니다)</p>
            <div class="verification-code">{st.session_state.verification_code}</div>
            <div class="timer">⏰ 남은 시간: {get_remaining_time() // 60}:{get_remaining_time() % 60:02d}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 인증번호 입력
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_code = st.text_input(
                "인증번호 입력",
                placeholder="4자리 숫자",
                max_chars=4,
                key="verification_input"
            )
        
        with col2:
            st.write("")
            st.write("")
            verify_button = st.button("✅ 인증하기", type="primary", use_container_width=True)
        
        # 인증 시도 횟수 표시
        if st.session_state.verification_attempts > 0:
            remaining_attempts = SMS_CONFIG['max_attempts'] - st.session_state.verification_attempts
            st.caption(f"⚠️ 남은 시도 횟수: {remaining_attempts}회")
        
        # 인증 확인
        if verify_button:
            if not user_code:
                st.warning("⚠️ 인증번호를 입력해주세요.")
            elif st.session_state.verification_attempts >= SMS_CONFIG['max_attempts']:
                st.error("❌ 최대 시도 횟수를 초과했습니다. 처음부터 다시 시도해주세요.")
            elif user_code == st.session_state.verification_code:
                st.session_state.is_verified = True
                
                # 비지정석이 있는지 확인
                has_unassigned = any(
                    pd.isna(row['좌석번호']) or row['좌석번호'] == ''
                    for _, row in user_data.iterrows()
                )
                
                if has_unassigned:
                    st.session_state.step = 2.7  # 좌석 선택 단계
                    st.success("✅ 인증 성공! 좌석 선택 페이지로 이동합니다...")
                else:
                    st.session_state.step = 3  # 바로 QR 발권
                    st.success("✅ 인증 성공! QR 발권 페이지로 이동합니다...")
                
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.verification_attempts += 1
                remaining = SMS_CONFIG['max_attempts'] - st.session_state.verification_attempts
                st.error(f"❌ 인증번호가 일치하지 않습니다. (남은 시도: {remaining}회)")
        
        # 재발송 및 이전 버튼
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 인증번호 재발송", use_container_width=True):
                code = generate_verification_code()
                send_sms_verification(phone_number, code)
                st.success("✅ 새로운 인증번호가 발송되었습니다!")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("← 이전", use_container_width=True):
                st.session_state.step = 2
                st.session_state.verification_code = None
                st.session_state.verification_time = None
                st.session_state.verification_attempts = 0
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== Step 2.7: 좌석 선택 ====================
elif st.session_state.step == 2.7:
    user_data = st.session_state.verified_user
    perf = st.session_state.selected_performance
    
    # 비지정석 개수 확인
    unassigned_count = sum(
        1 for _, row in user_data.iterrows()
        if pd.isna(row['좌석번호']) or row['좌석번호'] == ''
    )
    
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("🪑 좌석 선택")
    
    st.info(f"🎫 비지정석 **{unassigned_count}장**의 좌석을 선택해주세요!")
    
    # 선택 가능한 좌석 목록
    all_seats = get_available_seats(perf['공연명'])
    
    if not all_seats:
        st.error("❌ 선택 가능한 좌석이 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("← 이전", use_container_width=True):
            st.session_state.step = 2.5
            st.rerun()
    else:
        occupied_seats = get_occupied_seats(perf['공연명'], perf['공연일시'], perf['회차'])
        
        # 이미 예약된 좌석 제외
        available_seats = [
            seat for seat in all_seats
            if seat['seat_id'] not in occupied_seats and seat['seat_id'] not in st.session_state.selected_seats
        ]
        
        # 구역별로 그룹화
        sections = {}
        for seat in available_seats:
            section_name = seat['section']
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(seat)
        
        # 구역별 표시
        st.write("### 🎭 구역별 좌석")
        
        for section_name, seats in sections.items():
            with st.expander(f"{section_name} ({len(seats)}석 가능)", expanded=True):
                # 가격 정보
                st.write(f"💰 가격: {seats[0]['price']:,}원")
                
                # 좌석 선택 (multiselect)
                seat_options = [seat['seat_id'] for seat in seats]
                
                # 이미 선택된 좌석 중 이 구역에 속한 것들
                selected_in_section = [s for s in st.session_state.selected_seats if s in seat_options]
                
                # 남은 선택 가능 개수
                remaining = unassigned_count - len(st.session_state.selected_seats)
                
                selected = st.multiselect(
                    f"좌석 선택 (최대 {remaining}석)",
                    seat_options,
                    default=selected_in_section,
                    key=f"seats_{section_name}",
                    max_selections=remaining if remaining > 0 else 0
                )
                
                # 선택 업데이트
                st.session_state.selected_seats = [
                    s for s in st.session_state.selected_seats if s not in seat_options
                ]
                st.session_state.selected_seats.extend(selected)
        
        # 선택된 좌석 요약
        if st.session_state.selected_seats:
            st.write("### ✅ 선택된 좌석")
            st.success(f"{', '.join(sorted(st.session_state.selected_seats))}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 다음 단계 버튼
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("← 이전", use_container_width=True):
                st.session_state.step = 2.5
                st.session_state.selected_seats = []
                st.rerun()
        
        with col2:
            if len(st.session_state.selected_seats) == unassigned_count:
                if st.button("✅ 좌석 확정", type="primary", use_container_width=True):
                    # 선택한 좌석을 user_data에 반영
                    unassigned_idx = 0
                    for idx, row in user_data.iterrows():
                        if pd.isna(row['좌석번호']) or row['좌석번호'] == '':
                            st.session_state.verified_user.at[idx, '좌석번호'] = st.session_state.selected_seats[unassigned_idx]
                            unassigned_idx += 1
                    
                    st.session_state.step = 3
                    st.success("✅ 좌석이 확정되었습니다!")
                    time.sleep(1)
                    st.rerun()
            else:
                remaining = unassigned_count - len(st.session_state.selected_seats)
                st.button(
                    f"좌석 {remaining}개 더 선택해주세요",
                    disabled=True,
                    use_container_width=True
                )

# ==================== Step 3: QR 발권 ====================
elif st.session_state.step == 3:
    # 인증 확인
    if not st.session_state.is_verified:
        st.error("❌ 인증이 필요합니다.")
        st.session_state.step = 2.5
        st.rerun()
    
    user_data = st.session_state.verified_user
    
    st.markdown(f'''
    <div class="success-box">
        <h3>✅ {user_data.iloc[0]['이름']}님, 본인 인증이 완료되었습니다!</h3>
        <p>총 <strong>{len(user_data)}장</strong>의 티켓이 있습니다.</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 예매 정보 표시
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("📋 예매 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**예매번호:** {user_data.iloc[0]['예매번호']}")
        st.write(f"**이름:** {user_data.iloc[0]['이름']}")
        st.write(f"**전화번호:** {user_data.iloc[0]['전화번호']}")
    
    with col2:
        st.write(f"**공연명:** {user_data.iloc[0]['공연명']}")
        st.write(f"**공연일시:** {user_data.iloc[0]['공연일시']} {user_data.iloc[0]['회차']}")
        st.write(f"**티켓 수량:** {len(user_data)}장")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # QR 발권 버튼
    if st.button("🎫 QR 입장권 발급 (전체)", type="primary", use_container_width=True):
        issue_time = datetime.now()
        expire_time = issue_time + timedelta(hours=4)
        
        st.markdown("---")
        st.subheader(f"🎫 발급된 티켓 ({len(user_data)}장)")
        
        for idx, row in user_data.iterrows():
            ticket_data = {
                "예매번호": row['예매번호'],
                "이름": row['이름'],
                "공연명": row['공연명'],
                "공연일시": row['공연일시'],
                "회차": row['회차'],
                "좌석번호": row['좌석번호'] if pd.notna(row['좌석번호']) and row['좌석번호'] != '' else '비지정석',
                "발급시간": issue_time.strftime("%Y-%m-%d %H:%M:%S"),
                "만료시간": expire_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            qr_image = generate_qr_code(ticket_data)
            
            if qr_image:
                with st.container():
                    st.markdown(f'''
                    <div class="ticket-card">
                        <h4>🎫 티켓 #{idx + 1}</h4>
                        <p>좌석: <strong>{ticket_data['좌석번호']}</strong></p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col2:
                        st.image(qr_image, width=300)
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.download_button(
                                label="💾 저장",
                                data=qr_image,
                                file_name=f"ticket_{row['예매번호']}_{idx+1}.png",
                                mime="image/png",
                                use_container_width=True
                            )
                        
                        with col_b:
                            ticket_json = json.dumps(ticket_data)
                            share_url = f"?ticket={ticket_json}"
                            
                            if st.button(f"📤 공유", key=f"share_{idx}", use_container_width=True):
                                st.info(f"📱 동반자에게 이 링크를 전송하세요")
                        
                        st.caption(f"⏰ 유효시간: {expire_time.strftime('%Y-%m-%d %H:%M')}까지")
                    
                    st.markdown("---")
        
        if st.button("🔄 처음으로 돌아가기", use_container_width=True):
            st.session_state.step = 1
            st.session_state.verified_user = None
            st.session_state.verification_code = None
            st.session_state.verification_time = None
            st.session_state.verification_attempts = 0
            st.session_state.is_verified = False
            st.session_state.selected_seats = []
            st.rerun()

# ==================== Step 4: 스탬프북 ====================
elif st.session_state.step == 4:
    st.markdown('<div class="step-card">', unsafe_allow_html=True)
    st.subheader("🎁 환영합니다! 지역 할인 혜택")
    
    st.success("✅ 동반자 정보가 등록되었습니다!")
    
    st.write("### 📚 나의 스탬프북")
    
    for benefit in STAMP_BENEFITS:
        with st.expander(f"🎟️ {benefit['name']}", expanded=True):
            st.write(f"**설명:** {benefit['description']}")
            st.write(f"**이용 가능 장소:** {benefit['location']}")
            st.write(f"**유효기간:** {benefit['valid_days']}일")
            
            if st.button(f"사용하기", key=benefit['name'], use_container_width=True):
                st.info("🎉 혜택이 적용되었습니다! 제휴 매장에서 이 화면을 보여주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🏠 홈으로", use_container_width=True):
        st.session_state.is_companion = False
        st.session_state.companion_ticket_data = None
        st.session_state.step = 1
        st.rerun()

# 푸터
st.markdown("---")
st.caption("🎫 티켓츠 QR 발권 시스템 v2.1 - Phase 2.1 (좌석 선택 UI)")
