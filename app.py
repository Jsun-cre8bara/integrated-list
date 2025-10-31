"""
티켓츠 예매 명부 통합 웹앱 (Streamlit)
티켓링크, 인터파크, 예스24 자동 통합
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 페이지 설정
st.set_page_config(
    page_title="티켓츠 통합명부",
    page_icon="🎭",
    layout="wide"
)

def safe_str(value, max_length=1000):
    """안전하게 문자열로 변환 (길이 제한 포함)"""
    if pd.isna(value) or value == '':
        return ''
    str_value = str(value).strip()
    if len(str_value) > max_length:
        return str_value[:max_length] + '...'
    return str_value


def parse_datetime(row, date_col, time_col=None):
    """날짜와 시간을 yy-mm-dd 00:00시 형식으로 변환"""
    try:
        date_val = row.get(date_col, '')
        
        if pd.isna(date_val) or date_val == '':
            return ''
        
        # 날짜 파싱
        if isinstance(date_val, datetime):
            date_str = date_val.strftime('%y-%m-%d')
        else:
            date_str = str(date_val).strip()
            # 다양한 형식 처리
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) >= 3:
                    year = parts[0][-2:] if len(parts[0]) > 2 else parts[0].zfill(2)
                    month = parts[1].zfill(2)
                    day = parts[2].split()[0].zfill(2)
                    date_str = f"{year}-{month}-{day}"
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) >= 3:
                    year = parts[0][-2:] if len(parts[0]) > 2 else parts[0].zfill(2)
                    month = parts[1].zfill(2)
                    day = parts[2].split()[0].zfill(2)
                    date_str = f"{year}-{month}-{day}"
        
        # 시간 추가 (별도 시간 컬럼이 있는 경우)
        if time_col and time_col in row:
            time_val = row[time_col]
            if not pd.isna(time_val) and time_val != '':
                time_str = str(time_val).strip()
                if ':' in time_str:
                    time_part = time_str.split(':')
                    if len(time_part) >= 2:
                        hour = time_part[0].strip().zfill(2)
                        minute = time_part[1].strip()[:2].zfill(2)
                        return f"{date_str} {hour}:{minute}시"
        
        # 날짜 문자열에 이미 시간이 포함된 경우
        if ' ' in str(date_val):
            parts = str(date_val).split()
            if len(parts) >= 2 and ':' in parts[1]:
                time_part = parts[1].split(':')
                if len(time_part) >= 2:
                    hour = time_part[0].strip().zfill(2)
                    minute = time_part[1].strip()[:2].zfill(2)
                    return f"{date_str} {hour}:{minute}시"
        
        return f"{date_str} 00:00시"
    except:
        return safe_str(date_val)


def process_ticketlink(df, source_name):
    """티켓링크 데이터 처리"""
    result = pd.DataFrame()
    
    result['예매처'] = source_name
    
    if '관람일' in df.columns:
        result['공연일시'] = df.apply(
            lambda row: parse_datetime(row, '관람일', '회차/시간'), 
            axis=1
        )
    else:
        result['공연일시'] = ''
    
    result['예매자이름'] = df['성명'].apply(safe_str) if '성명' in df.columns else ''
    result['매수'] = df['매수'].apply(lambda x: safe_str(x, 50)) if '매수' in df.columns else ''
    result['좌석번호'] = df['좌석번호'].apply(lambda x: safe_str(x, 200)) if '좌석번호' in df.columns else ''
    result['연락처'] = df['연락처'].apply(lambda x: safe_str(x, 100)) if '연락처' in df.columns else ''
    
    return result


def process_interpark(df, source_name):
    """인터파크 데이터 처리"""
    result = pd.DataFrame()
    
    result['예매처'] = source_name
    
    if '공연일시' in df.columns:
        result['공연일시'] = df.apply(
            lambda row: parse_datetime(row, '공연일시'), 
            axis=1
        )
    else:
        result['공연일시'] = ''
    
    result['예매자이름'] = df['예매자'].apply(safe_str) if '예매자' in df.columns else ''
    result['매수'] = df['판매좌석수'].apply(lambda x: safe_str(x, 50)) if '판매좌석수' in df.columns else ''
    result['좌석번호'] = df['좌석정보'].apply(lambda x: safe_str(x, 200)) if '좌석정보' in df.columns else ''
    result['연락처'] = df['전화번호'].apply(lambda x: safe_str(x, 100)) if '전화번호' in df.columns else ''
    
    return result


def process_yes24(df, source_name):
    """예스24 데이터 처리"""
    result = pd.DataFrame()
    
    result['예매처'] = source_name
    
    if '공연일자' in df.columns:
        result['공연일시'] = df.apply(
            lambda row: parse_datetime(row, '공연일자'), 
            axis=1
        )
    else:
        result['공연일시'] = ''
    
    result['예매자이름'] = df['예매자명'].apply(safe_str) if '예매자명' in df.columns else ''
    result['매수'] = df['매수'].apply(lambda x: safe_str(x, 50)) if '매수' in df.columns else ''
    result['좌석번호'] = df['좌석정보'].apply(lambda x: safe_str(x, 200)) if '좌석정보' in df.columns else ''
    result['연락처'] = df['비상연락처'].apply(lambda x: safe_str(x, 100)) if '비상연락처' in df.columns else ''
    
    return result


def detect_source_type(df, filename):
    """파일의 헤더를 보고 어느 예매처인지 판단"""
    columns = [str(col).strip() for col in df.columns]
    
    # 티켓링크 특징
    if '회차/시간' in columns or '관람일' in columns:
        return 'ticketlink'
    
    # 인터파크 특징
    if '판매좌석수' in columns or '티켓배송' in columns:
        return 'interpark'
    
    # 예스24 특징  
    if '공연일자' in columns and '예매자명' in columns:
        return 'yes24'
    
    # 파일명으로 추측
    filename_lower = filename.lower()
    if 'ticket' in filename_lower or '티켓링크' in filename:
        return 'ticketlink'
    elif 'inter' in filename_lower or '인터파크' in filename:
        return 'interpark'
    elif 'yes' in filename_lower or '예스' in filename:
        return 'yes24'
    
    return 'unknown'


def merge_uploaded_files(uploaded_files):
    """업로드된 파일들을 통합"""
    all_data = []
    processing_log = []
    
    for uploaded_file in uploaded_files:
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(uploaded_file, dtype=str)
            
            # 파일명 (확장자 제외)
            source_name = uploaded_file.name.rsplit('.', 1)[0]
            
            # 예매처 타입 자동 감지
            source_type = detect_source_type(df, uploaded_file.name)
            
            processing_log.append({
                'file': uploaded_file.name,
                'rows': len(df),
                'type': source_type
            })
            
            # 예매처별 처리
            if source_type == 'ticketlink':
                result_df = process_ticketlink(df, source_name)
            elif source_type == 'interpark':
                result_df = process_interpark(df, source_name)
            elif source_type == 'yes24':
                result_df = process_yes24(df, source_name)
            else:
                processing_log[-1]['error'] = '예매처를 자동 감지할 수 없습니다'
                continue
            
            if not result_df.empty:
                all_data.append(result_df)
                processing_log[-1]['processed'] = len(result_df)
            
        except Exception as e:
            processing_log.append({
                'file': uploaded_file.name,
                'error': str(e)
            })
    
    if not all_data:
        return None, processing_log
    
    # 모든 데이터 합치기
    merged_df = pd.concat(all_data, ignore_index=True)
    
    # 컬럼 순서 정리
    final_columns = ['예매처', '공연일시', '예매자이름', '매수', '좌석번호', '연락처']
    merged_df = merged_df[final_columns]
    
    return merged_df, processing_log


# 메인 UI
st.title("🎭 티켓츠 예매 명부 통합")
st.markdown("---")

# 안내 메시지
with st.expander("📖 사용 방법", expanded=True):
    st.markdown("""
    ### 지원 예매처
    - **티켓링크**: 관람일, 회차/시간, 성명, 매수, 좌석번호, 연락처
    - **인터파크**: 공연일시, 예매자, 판매좌석수, 좌석정보, 전화번호
    - **예스24**: 공연일자, 예매자명, 매수, 좌석정보, 비상연락처
    
    ### 사용 방법
    1. 아래에서 엑셀 파일들을 선택하거나 드래그하세요
    2. '통합하기' 버튼을 클릭하세요
    3. 통합된 명부를 다운로드하세요!
    
    💡 **팁**: 파일명에 예매처 이름(티켓링크/인터파크/예스24)을 포함하면 더 정확합니다.
    """)

st.markdown("---")

# 파일 업로드
uploaded_files = st.file_uploader(
    "📁 엑셀 파일을 선택하세요 (여러 개 가능)",
    type=['xlsx', 'xls'],
    accept_multiple_files=True,
    help="티켓링크, 인터파크, 예스24 엑셀 파일을 모두 선택하세요"
)

# 파일이 업로드되면
if uploaded_files:
    st.success(f"✅ {len(uploaded_files)}개의 파일이 업로드되었습니다!")
    
    # 업로드된 파일 목록
    with st.expander("📋 업로드된 파일 목록", expanded=True):
        for i, file in enumerate(uploaded_files, 1):
            st.write(f"{i}. {file.name}")
    
    st.markdown("---")
    
    # 통합하기 버튼
    if st.button("🔗 통합하기", type="primary", use_container_width=True):
        with st.spinner('📊 파일을 분석하고 통합하는 중...'):
            merged_df, processing_log = merge_uploaded_files(uploaded_files)
        
        # 처리 결과 표시
        st.markdown("### 📝 처리 결과")
        
        for log in processing_log:
            if 'error' in log:
                st.error(f"❌ {log['file']}: {log['error']}")
            else:
                st.success(f"✅ {log['file']} ({log['rows']}행) → {log['type']} 형식으로 처리 ({log.get('processed', 0)}건)")
        
        if merged_df is not None:
            st.markdown("---")
            st.success(f"✨ 통합 완료! 총 {len(merged_df)}건의 예매 정보가 통합되었습니다.")
            
            # 통계 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 예매처별 통계")
                stats = merged_df['예매처'].value_counts().reset_index()
                stats.columns = ['예매처', '건수']
                st.dataframe(stats, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### 📊 총계")
                st.metric("전체 예매 건수", f"{len(merged_df):,}건")
                st.metric("예매처 수", f"{len(stats)}개")
            
            st.markdown("---")
            
            # 데이터 미리보기
            st.markdown("### 👀 통합 명부 미리보기")
            st.dataframe(merged_df.head(10), use_container_width=True)
            
            if len(merged_df) > 10:
                st.info(f"💡 전체 {len(merged_df)}건 중 10건만 표시됩니다. 전체 데이터는 다운로드하세요.")
            
            st.markdown("---")
            
            # 엑셀 파일로 변환
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                merged_df.to_excel(writer, index=False, sheet_name='통합명부')
            
            excel_data = output.getvalue()
            
            # 다운로드 버튼
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"통합_예매명부_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 통합 명부 다운로드",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
        else:
            st.error("❌ 통합할 수 있는 데이터가 없습니다.")
            st.markdown("""
            ### 💡 해결 방법
            - 엑셀 파일이 올바른 형식인지 확인하세요
            - 파일명에 예매처 이름을 포함해보세요 (예: 티켓링크_공연명.xlsx)
            - 지원되는 헤더가 있는지 확인하세요
            """)

else:
    st.info("👆 위에서 엑셀 파일을 업로드해주세요!")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🎭 티켓츠(tCATS) 예매 명부 통합 시스템</p>
    <p style='font-size: 0.8em;'>티켓링크 / 인터파크 / 예스24 자동 통합</p>
</div>
""", unsafe_allow_html=True)
