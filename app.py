import streamlit as st
import pandas as pd
from io import BytesIO
import sqlite3
from datetime import datetime
import re

# 페이지 설정
st.set_page_config(
    page_title="티켓츠 예매 관리",
    page_icon="📋",
    layout="wide"
)

# 데이터베이스 초기화
@st.cache_resource
def init_db():
    """데이터베이스 초기화"""
    conn = sqlite3.connect('ticketz.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_name TEXT NOT NULL,
            performance_date TEXT NOT NULL,
            performance_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            total_reservations INTEGER DEFAULT 0,
            UNIQUE(performance_name, performance_date, performance_time)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            reservation_number TEXT,
            name TEXT,
            phone TEXT,
            seat_info TEXT,
            quantity INTEGER DEFAULT 0,
            status TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (performance_id) REFERENCES performances (id)
        )
    ''')
    
    conn.commit()
    return conn

conn = init_db()

# 제목
st.title("📋 티켓츠 예매 관리 시스템")
st.markdown("---")

# 탭 생성
tab1, tab2 = st.tabs(["📝 통합명부 작성", "📋 예약 리스트"])

# ============= 탭 1: 통합명부 작성 =============
with tab1:
    st.header("📝 통합명부 작성")
    
    # 사이드바 대신 컬럼 사용
    col_upload, col_content = st.columns([1, 2])
    
    with col_upload:
        st.markdown("### 📁 파일 업로드")
        uploaded_files = st.file_uploader(
            "Excel 파일 선택",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="file_uploader"
        )
        
        st.markdown("---")
        st.markdown("**📌 지원 예매처**")
        st.markdown("- 인터파크")
        st.markdown("- 티켓링크")
        st.markdown("- 예스24")
    
    with col_content:
        def extract_performance_info(uploaded_file):
            """Excel 파일에서 공연 정보 추출"""
            try:
                file_name = uploaded_file.name
                
                # 모든 플랫폼에 대해 넓게 헤더 읽기
                df_header = pd.read_excel(uploaded_file, header=None, nrows=25)
                
                performance_name = ""
                performance_date = ""
                performance_time = ""
                source = ""
                
                # 파일명으로 플랫폼 감지
                if '티켓링크' in file_name or 'ticketlink' in file_name.lower():
                    source = '티켓링크'
                elif '인터파크' in file_name or 'interpark' in file_name.lower():
                    source = '인터파크'
                elif '예스24' in file_name or 'yes24' in file_name.lower():
                    source = '예스24'
                else:
                    source = '알 수 없음'
                
                # 모든 셀을 순회하며 정보 찾기
                for idx, row in df_header.iterrows():
                    for col_idx in range(min(10, len(row))):  # 최대 10개 컬럼까지 확인
                        cell_value = str(row.iloc[col_idx]) if col_idx < len(row) else ""
                        
                        if pd.isna(cell_value) or cell_value == 'nan':
                            continue
                        
                        # 공연명/상품명 찾기
                        if not performance_name and ('공연명' in cell_value or '상품명' in cell_value or '제목' in cell_value):
                            # 콜론(:) 뒤의 내용 추출
                            if ':' in cell_value or '：' in cell_value:
                                parts = re.split(r'[:：]', cell_value, 1)
                                if len(parts) > 1:
                                    performance_name = parts[1].strip()
                                    # 괄호나 추가 정보 제거
                                    performance_name = re.sub(r'\([^)]*\)', '', performance_name).strip()
                        
                        # 날짜 찾기 (YYYY.MM.DD 또는 YYYY-MM-DD 형식)
                        if not performance_date:
                            date_match = re.search(r'(\d{4})[.-](\d{2})[.-](\d{2})', cell_value)
                            if date_match:
                                performance_date = f"{date_match.group(1)}.{date_match.group(2)}.{date_match.group(3)}"
                        
                        # 시간 찾기 (HH:MM 형식)
                        if not performance_time:
                            time_match = re.search(r'(\d{1,2}):(\d{2})', cell_value)
                            if time_match and '조회' not in cell_value:  # "조회시간" 같은 건 제외
                                hour = time_match.group(1).zfill(2)
                                minute = time_match.group(2)
                                performance_time = f"{hour}:{minute}"
                
                # 정보가 추출되었는지 확인
                if performance_name or performance_date:
                    return {
                        'name': performance_name if performance_name else '(공연명 없음)',
                        'date': performance_date if performance_date else '(날짜 없음)',
                        'time': performance_time,
                        'source': source
                    }
                
                return None
                
            except Exception as e:
                st.error(f"파일 읽기 오류: {str(e)}")
                return None
        
        
        def parse_excel_file(uploaded_file):
            """Excel 파일 파싱"""
            try:
                file_name = uploaded_file.name
                
                if '인터파크' in file_name or 'interpark' in file_name.lower():
                    platform = '인터파크'
                    header_row = 5
                elif '티켓링크' in file_name or 'ticketlink' in file_name.lower():
                    platform = '티켓링크'
                    header_row = 5
                elif '예스24' in file_name or 'yes24' in file_name.lower():
                    platform = '예스24'
                    header_row = 19
                else:
                    return [], '알 수 없음'
                
                try:
                    df = pd.read_excel(uploaded_file, header=header_row, engine='openpyxl')
                except:
                    df = pd.read_excel(uploaded_file, header=header_row, engine='xlrd')
                
                result_data = []
                
                for idx, row in df.iterrows():
                    try:
                        if platform == '인터파크':
                            data = {
                                '예매처': '인터파크',
                                '예매번호': str(row.get('예매번호', '')),
                                '예매자명': str(row.get('예매자명', '')),
                                '연락처': str(row.get('휴대폰번호', '')),
                                '좌석정보': str(row.get('좌석정보', '')),
                                '매수': int(row.get('매수', 0)) if pd.notna(row.get('매수', 0)) else 0,
                                '배정상태': '지정' if pd.notna(row.get('좌석정보', '')) and str(row.get('좌석정보', '')) != '' else '비지정'
                            }
                            result_data.append(data)
                            
                        elif platform == '티켓링크':
                            data = {
                                '예매처': '티켓링크',
                                '예매번호': str(row.get('예매번호(연동사 예매번호)', '')),
                                '예매자명': str(row.get('성명', '')),
                                '연락처': str(row.get('연락처(SMS)', '')),
                                '좌석정보': str(row.get('좌석번호', '')),
                                '매수': int(row.get('매수', 0)) if pd.notna(row.get('매수', 0)) else 0,
                                '배정상태': '지정' if pd.notna(row.get('좌석번호', '')) and str(row.get('좌석번호', '')) != '' else '비지정'
                            }
                            result_data.append(data)
                            
                        elif platform == '예스24':
                            data = {
                                '예매처': '예스24',
                                '예매번호': str(row.get('주문번호', '')),
                                '예매자명': str(row.get('예매자명', '')),
                                '연락처': str(row.get('휴대폰번호', '')),
                                '좌석정보': str(row.get('좌석', '')),
                                '매수': int(row.get('매수', 0)) if pd.notna(row.get('매수', 0)) else 0,
                                '배정상태': '지정' if pd.notna(row.get('좌석', '')) and str(row.get('좌석', '')) != '' else '비지정'
                            }
                            result_data.append(data)
                            
                    except Exception as e:
                        continue
                
                return result_data, platform
                
            except Exception as e:
                return [], '오류'
        
        
        def save_to_database(performance_info, reservation_data):
            """데이터베이스에 저장"""
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    SELECT id FROM performances 
                    WHERE performance_name = ? AND performance_date = ? AND performance_time = ?
                ''', (performance_info['name'], performance_info['date'], performance_info['time']))
                
                result = cursor.fetchone()
                
                if result:
                    performance_id = result[0]
                    cursor.execute('''
                        UPDATE performances 
                        SET updated_at = ?, total_reservations = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), len(reservation_data), performance_id))
                    
                    cursor.execute('DELETE FROM reservations WHERE performance_id = ?', (performance_id,))
                    
                else:
                    cursor.execute('''
                        INSERT INTO performances (performance_name, performance_date, performance_time, created_at, updated_at, total_reservations)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (performance_info['name'], performance_info['date'], performance_info['time'], 
                          datetime.now().isoformat(), datetime.now().isoformat(), len(reservation_data)))
                    
                    performance_id = cursor.lastrowid
                
                for reservation in reservation_data:
                    cursor.execute('''
                        INSERT INTO reservations (performance_id, platform, reservation_number, name, phone, seat_info, quantity, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (performance_id, reservation['예매처'], reservation['예매번호'], reservation['예매자명'],
                          reservation['연락처'], reservation['좌석정보'], reservation['매수'], reservation['배정상태'],
                          datetime.now().isoformat()))
                
                conn.commit()
                return True, performance_id
                
            except Exception as e:
                conn.rollback()
                st.error(f"저장 오류: {str(e)}")
                return False, None
        
        
        # 메인 로직
        if uploaded_files:
            st.markdown("### 📊 업로드된 파일")
            for file in uploaded_files:
                st.info(f"**{file.name}** ({file.size:,} bytes)")
            
            st.markdown("---")
            
            # 공연 정보 추출
            if 'performance_info_extracted' not in st.session_state:
                st.session_state['performance_info_extracted'] = False
            
            if not st.session_state['performance_info_extracted']:
                if st.button("🔍 공연 정보 추출", type="primary", use_container_width=True):
                    perf_info = extract_performance_info(uploaded_files[0])
                    
                    if perf_info and (perf_info['name'] != '(공연명 없음)' or perf_info['date'] != '(날짜 없음)'):
                        st.session_state['extracted_performance_info'] = perf_info
                        st.session_state['performance_info_extracted'] = True
                        st.rerun()
                    else:
                        st.warning("⚠️ 자동으로 공연 정보를 추출할 수 없습니다.")
                        if perf_info:
                            st.info(f"""
                            **추출 시도 결과:**
                            - 공연명: {perf_info['name']}
                            - 날짜: {perf_info['date']}
                            - 시간: {perf_info['time'] if perf_info['time'] else '(없음)'}
                            
                            아래에서 직접 입력해주세요.
                            """)
                        st.session_state['manual_input'] = True
                        st.session_state['extracted_performance_info'] = perf_info if perf_info else {'name': '', 'date': '', 'time': ''}
            
            # 추출된 공연 정보 확인
            if st.session_state.get('performance_info_extracted'):
                perf_info = st.session_state['extracted_performance_info']
                
                st.success("✅ 공연 정보가 추출되었습니다!")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.info(f"""
                    ### 📋 추출된 공연 정보
                    
                    **공연명:** {perf_info['name']}  
                    **날짜:** {perf_info['date']}  
                    **시간(회차):** {perf_info['time'] if perf_info['time'] else '데이터에서 확인 필요'}  
                    
                    이 정보가 맞습니까?
                    """)
                
                with col2:
                    if st.button("✅ Yes", type="primary", use_container_width=True):
                        st.session_state['confirmed'] = True
                        st.session_state['performance_confirmed_info'] = perf_info
                        st.rerun()
                    
                    if st.button("❌ No", use_container_width=True):
                        st.session_state['manual_input'] = True
                        st.rerun()
            
            # 수동 입력
            if st.session_state.get('manual_input'):
                st.warning("### ✏️ 수동으로 공연 정보를 입력하세요")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    manual_name = st.text_input("공연명", value=st.session_state.get('extracted_performance_info', {}).get('name', ''))
                
                with col2:
                    manual_date = st.text_input("날짜 (YYYY.MM.DD)", value=st.session_state.get('extracted_performance_info', {}).get('date', ''))
                
                with col3:
                    manual_time = st.text_input("시간(회차) (HH:MM)", value="")
                
                if st.button("✅ 수동 입력 완료", type="primary"):
                    if manual_name and manual_date:
                        st.session_state['performance_confirmed_info'] = {
                            'name': manual_name,
                            'date': manual_date,
                            'time': manual_time,
                            'source': '수동 입력'
                        }
                        st.session_state['confirmed'] = True
                        st.rerun()
                    else:
                        st.error("공연명과 날짜는 필수 입력 항목입니다!")
            
            # 통합 및 저장
            if st.session_state.get('confirmed'):
                st.markdown("---")
                
                if st.button("🔄 통합하고 저장하기", type="primary", use_container_width=True):
                    with st.spinner("파일을 통합하고 저장하는 중..."):
                        all_data = []
                        
                        for uploaded_file in uploaded_files:
                            data, platform = parse_excel_file(uploaded_file)
                            all_data.extend(data)
                        
                        if all_data:
                            df_integrated = pd.DataFrame(all_data)
                            
                            success, performance_id = save_to_database(
                                st.session_state['performance_confirmed_info'],
                                all_data
                            )
                            
                            if success:
                                st.session_state['integrated_data'] = df_integrated
                                st.session_state['saved'] = True
                                st.success(f"✅ 총 {len(df_integrated)}건이 저장되었습니다!")
                                st.balloons()
                        else:
                            st.error("통합할 데이터가 없습니다.")
        
        else:
            st.info("👈 왼쪽에서 예매 파일을 업로드하세요!")

# ============= 탭 2: 예약 리스트 =============
with tab2:
    st.header("📋 예약 리스트")
    
    def get_all_performances():
        """모든 공연 목록 조회"""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT performance_name
            FROM performances
            ORDER BY performance_name
        ''')
        return [row[0] for row in cursor.fetchall()]
    
    
    def get_performance_sessions(performance_name):
        """특정 공연의 회차 목록 조회"""
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, performance_date, performance_time, updated_at, total_reservations
            FROM performances
            WHERE performance_name = ?
            ORDER BY performance_date, performance_time
        ''', (performance_name,))
        return cursor.fetchall()
    
    
    def get_reservations(performance_id):
        """특정 공연 회차의 예약 리스트 조회"""
        query = '''
            SELECT platform, reservation_number, name, phone, seat_info, quantity, status
            FROM reservations
            WHERE performance_id = ?
            ORDER BY platform, name
        '''
        df = pd.read_sql_query(query, conn, params=(performance_id,))
        df.columns = ['예매처', '예매번호', '예매자명', '연락처', '좌석정보', '매수', '배정상태']
        return df
    
    
    performances = get_all_performances()
    
    if not performances:
        st.warning("⚠️ 저장된 공연이 없습니다. '통합명부 작성' 탭에서 먼저 데이터를 저장해주세요.")
    else:
        st.markdown("## 🎭 공연 선택")
        selected_performance = st.selectbox(
            "조회할 공연을 선택하세요",
            performances,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if selected_performance:
            sessions = get_performance_sessions(selected_performance)
            
            st.markdown("## 📅 공연 회차 목록")
            
            for session in sessions:
                session_id, perf_date, perf_time, updated_at, total = session
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 1])
                
                with col1:
                    st.markdown(f"### 📅 {perf_date}")
                
                with col2:
                    st.markdown(f"**⏰ {perf_time if perf_time else '시간 미정'}**")
                
                with col3:
                    update_time = datetime.fromisoformat(updated_at)
                    st.markdown(f"🔄 {update_time.strftime('%Y-%m-%d %H:%M')}")
                
                with col4:
                    st.markdown(f"**👥 {total}건**")
                
                with col5:
                    if st.button("📋 조회", key=f"view_{session_id}", use_container_width=True):
                        st.session_state['selected_session_id'] = session_id
                        st.session_state['selected_session_info'] = {
                            'name': selected_performance,
                            'date': perf_date,
                            'time': perf_time,
                            'total': total
                        }
                        st.rerun()
                
                st.markdown("---")
            
            # 선택된 회차의 예약 리스트 표시
            if 'selected_session_id' in st.session_state:
                st.markdown("---")
                st.markdown("# 📊 예약 상세 정보")
                
                session_info = st.session_state['selected_session_info']
                
                # 선택된 회차 강조 표시
                st.success(f"✅ 조회 중: **{session_info['name']}** - {session_info['date']} {session_info['time'] if session_info['time'] else '시간 미정'}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    **공연:** {session_info['name']}  
                    **날짜:** {session_info['date']}  
                    **시간:** {session_info['time'] if session_info['time'] else '시간 미정'}
                    """)
                
                with col2:
                    st.metric("총 예약", f"{session_info['total']}건")
                
                # 예약 데이터 조회
                with st.spinner("예약 데이터를 조회하는 중..."):
                    df_reservations = get_reservations(st.session_state['selected_session_id'])
                
                # 디버깅 정보
                st.info(f"💾 데이터베이스에서 {len(df_reservations)}건의 예약을 찾았습니다")
                st.write(f"**DataFrame shape:** {df_reservations.shape}")
                st.write(f"**DataFrame columns:** {df_reservations.columns.tolist()}")
                
                # 강제로 구분선 추가
                st.markdown("---")
                st.markdown("### 🔽 아래에 예약 데이터가 표시됩니다")
                st.markdown("---")
                
                if len(df_reservations) > 0:
                    # 통계
                    col3, col4, col5 = st.columns(3)
                    
                    with col3:
                        total_seats = df_reservations['매수'].sum()
                        st.metric("총 좌석", f"{total_seats}석")
                    
                    with col4:
                        assigned = len(df_reservations[df_reservations['배정상태'] == '지정'])
                        st.metric("지정석", f"{assigned}건")
                    
                    with col5:
                        unassigned = len(df_reservations[df_reservations['배정상태'] == '비지정'])
                        st.metric("비지정석", f"{unassigned}건")
                    
                    st.markdown("---")
                    
                    # 필터링
                    st.markdown("### 🔍 필터 및 검색")
                    
                    filter_col1, filter_col2, filter_col3 = st.columns(3)
                    
                    with filter_col1:
                        platform_filter = st.multiselect(
                            "예매처",
                            df_reservations['예매처'].unique().tolist(),
                            df_reservations['예매처'].unique().tolist()
                        )
                    
                    with filter_col2:
                        status_filter = st.multiselect(
                            "배정 상태",
                            ['지정', '비지정'],
                            ['지정', '비지정']
                        )
                    
                    with filter_col3:
                        search_text = st.text_input("예매자명 검색")
                    
                    # 필터 적용
                    filtered_df = df_reservations.copy()
                    
                    if platform_filter:
                        filtered_df = filtered_df[filtered_df['예매처'].isin(platform_filter)]
                    
                    if status_filter:
                        filtered_df = filtered_df[filtered_df['배정상태'].isin(status_filter)]
                    
                    if search_text:
                        filtered_df = filtered_df[filtered_df['예매자명'].str.contains(search_text, na=False)]
                    
                    st.markdown(f"**검색 결과: {len(filtered_df)}건**")
                    
                    # 데이터 테이블
                    st.dataframe(filtered_df, use_container_width=True, height=500)
                    
                    # 다운로드
                    def create_download_excel(df):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='예약리스트')
                        output.seek(0)
                        return output
                    
                    excel_data = create_download_excel(filtered_df)
                    st.download_button(
                        label="📥 Excel 다운로드",
                        data=excel_data,
                        file_name=f"예약리스트_{session_info['name']}_{session_info['date']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                else:
                    st.error("❌ 해당 회차의 예약 데이터가 없습니다!")
                    st.warning("""
                    **가능한 원인:**
                    1. 통합명부 작성 시 저장이 제대로 안됨
                    2. 공연 정보만 저장되고 예약 데이터는 저장 안됨
                    
                    **해결 방법:**
                    1. "📝 통합명부 작성" 탭으로 이동
                    2. 같은 파일을 다시 업로드
                    3. "🔄 통합하고 저장하기" 버튼 클릭
                    4. "✅ 총 XX건이 저장되었습니다!" 메시지 확인
                    """)
