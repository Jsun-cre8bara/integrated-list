import streamlit as st
import pandas as pd
from io import BytesIO
import xlrd
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="티켓츠 예매 명부 통합",
    page_icon="📋",
    layout="wide"
)

# 제목
st.title("📋 티켓츠 예매 명부 통합")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("📁 파일 업로드")
    st.markdown("인터파크, 티켓링크, 예스24 파일을 업로드하세요")
    
    uploaded_files = st.file_uploader(
        "Excel 파일 선택 (여러 개 가능)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True
    )
    
    st.markdown("---")
    st.markdown("### 📌 지원 예매처")
    st.markdown("- 인터파크 (6행 헤더)")
    st.markdown("- 티켓링크 (6행 헤더)")
    st.markdown("- 예스24 (20행 헤더)")


def detect_platform(df, file_name):
    """예매처 자동 감지"""
    file_name_lower = file_name.lower()
    
    if '인터파크' in file_name or 'interpark' in file_name_lower:
        return '인터파크'
    elif '티켓링크' in file_name or 'ticketlink' in file_name_lower:
        return '티켓링크'
    elif '예스24' in file_name or 'yes24' in file_name_lower:
        return '예스24'
    else:
        # 파일명으로 감지 안되면 첫 번째 파일로 추정
        return '알 수 없음'


def parse_excel_file(uploaded_file):
    """Excel 파일 파싱"""
    try:
        file_name = uploaded_file.name
        platform = detect_platform(None, file_name)
        
        # 플랫폼별 헤더 행 설정
        if platform == '예스24':
            header_row = 19  # 20행 (0부터 시작하므로 19)
        else:
            header_row = 5   # 6행 (0부터 시작하므로 5)
        
        # Excel 파일 읽기
        try:
            df = pd.read_excel(uploaded_file, header=header_row, engine='openpyxl')
        except:
            df = pd.read_excel(uploaded_file, header=header_row, engine='xlrd')
        
        # 플랫폼별 데이터 추출
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
                        '예매번호': str(row.get('주문번호', '')),
                        '예매자명': str(row.get('예매자', '')),
                        '연락처': str(row.get('휴대폰', '')),
                        '좌석정보': str(row.get('좌석', '')),
                        '매수': int(row.get('수량', 0)) if pd.notna(row.get('수량', 0)) else 0,
                        '배정상태': '지정' if pd.notna(row.get('좌석', '')) and str(row.get('좌석', '')) != '' else '비지정'
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
        st.error(f"파일 읽기 오류: {str(e)}")
        return [], '오류'


def create_download_excel(df):
    """Excel 다운로드 파일 생성"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='통합명부')
    output.seek(0)
    return output


# 메인 로직
if uploaded_files:
    st.header("📊 업로드된 파일")
    
    # 파일 정보 표시
    cols = st.columns(len(uploaded_files))
    for idx, (col, file) in enumerate(zip(cols, uploaded_files)):
        with col:
            st.info(f"**{file.name}**\n\n크기: {file.size:,} bytes")
    
    st.markdown("---")
    
    # 통합 버튼
    if st.button("🔄 통합하기", type="primary", use_container_width=True):
        with st.spinner("파일을 통합하는 중..."):
            all_data = []
            platform_counts = {}
            
            # 각 파일 파싱
            for uploaded_file in uploaded_files:
                data, platform = parse_excel_file(uploaded_file)
                all_data.extend(data)
                platform_counts[platform] = platform_counts.get(platform, 0) + len(data)
            
            if all_data:
                # 데이터프레임 생성
                df_integrated = pd.DataFrame(all_data)
                
                # 세션 스테이트에 저장
                st.session_state['integrated_data'] = df_integrated
                st.session_state['platform_counts'] = platform_counts
                
                st.success(f"✅ 총 {len(df_integrated)}건의 예매 데이터가 통합되었습니다!")
            else:
                st.error("통합할 데이터가 없습니다.")

# 통합된 데이터 표시
if 'integrated_data' in st.session_state:
    df = st.session_state['integrated_data']
    platform_counts = st.session_state['platform_counts']
    
    st.markdown("---")
    st.header("📋 통합 예약 리스트")
    
    # 통계 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 예약", f"{len(df):,}건")
    
    with col2:
        total_seats = df['매수'].sum()
        st.metric("총 좌석", f"{total_seats:,}석")
    
    with col3:
        assigned = len(df[df['배정상태'] == '지정'])
        st.metric("지정석", f"{assigned:,}건")
    
    with col4:
        unassigned = len(df[df['배정상태'] == '비지정'])
        st.metric("비지정석", f"{unassigned:,}건")
    
    # 예매처별 통계
    st.markdown("### 📊 예매처별 현황")
    platform_cols = st.columns(len(platform_counts))
    for idx, (platform, count) in enumerate(platform_counts.items()):
        with platform_cols[idx]:
            st.info(f"**{platform}**\n\n{count}건")
    
    st.markdown("---")
    
    # 필터링 옵션
    st.markdown("### 🔍 필터 및 검색")
    
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        platform_filter = st.multiselect(
            "예매처 선택",
            options=df['예매처'].unique().tolist(),
            default=df['예매처'].unique().tolist()
        )
    
    with filter_col2:
        status_filter = st.multiselect(
            "배정 상태",
            options=['지정', '비지정'],
            default=['지정', '비지정']
        )
    
    with filter_col3:
        search_text = st.text_input("예매자명 검색", placeholder="이름 입력...")
    
    # 필터 적용
    filtered_df = df.copy()
    
    if platform_filter:
        filtered_df = filtered_df[filtered_df['예매처'].isin(platform_filter)]
    
    if status_filter:
        filtered_df = filtered_df[filtered_df['배정상태'].isin(status_filter)]
    
    if search_text:
        filtered_df = filtered_df[filtered_df['예매자명'].str.contains(search_text, na=False)]
    
    st.markdown(f"**검색 결과: {len(filtered_df)}건**")
    
    # 데이터 테이블 표시
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=500,
        column_config={
            "예매처": st.column_config.TextColumn("예매처", width="small"),
            "예매번호": st.column_config.TextColumn("예매번호", width="medium"),
            "예매자명": st.column_config.TextColumn("예매자명", width="small"),
            "연락처": st.column_config.TextColumn("연락처", width="medium"),
            "좌석정보": st.column_config.TextColumn("좌석정보", width="large"),
            "매수": st.column_config.NumberColumn("매수", width="small"),
            "배정상태": st.column_config.TextColumn("배정상태", width="small"),
        }
    )
    
    st.markdown("---")
    
    # 다운로드 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # 전체 데이터 다운로드
        excel_data = create_download_excel(df)
        st.download_button(
            label="📥 전체 다운로드 (Excel)",
            data=excel_data,
            file_name=f"통합명부_전체_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # 필터링된 데이터 다운로드
        if len(filtered_df) < len(df):
            excel_filtered = create_download_excel(filtered_df)
            st.download_button(
                label="📥 필터 결과 다운로드",
                data=excel_filtered,
                file_name=f"통합명부_필터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

else:
    # 안내 메시지
    st.info("👈 왼쪽 사이드바에서 예매 파일을 업로드하고 통합 버튼을 클릭하세요!")
    
    st.markdown("---")
    st.markdown("### 📖 사용 방법")
    st.markdown("""
    1. **파일 업로드**: 인터파크, 티켓링크, 예스24 Excel 파일을 업로드
    2. **통합하기**: '🔄 통합하기' 버튼 클릭
    3. **확인**: 화면에서 통합된 예약 리스트 확인
    4. **검색/필터**: 예매처, 배정 상태, 이름으로 필터링
    5. **다운로드**: 통합된 데이터를 Excel로 다운로드
    """)
    
    st.markdown("---")
    st.markdown("### ✨ 주요 기능")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📊 실시간 통계**
        - 총 예약 건수
        - 총 좌석 수
        - 지정석/비지정석 현황
        - 예매처별 통계
        """)
    
    with col2:
        st.markdown("""
        **🔍 강력한 검색**
        - 예매처별 필터링
        - 배정 상태별 필터링
        - 예매자명 검색
        - 실시간 결과 업데이트
        """)
