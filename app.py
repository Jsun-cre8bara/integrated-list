"""
티켓츠 예매 명부 통합 웹앱 (실제 파일 구조 반영)
인터파크, 티켓링크, 예스24 자동 통합
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re

# 페이지 설정
st.set_page_config(
    page_title="티켓츠 통합명부",
    page_icon="🎭",
    layout="wide"
)


def safe_str(value, max_length=1000):
    """안전하게 문자열로 변환"""
    if pd.isna(value) or value == '':
        return ''
    str_value = str(value).strip()
    if len(str_value) > max_length:
        return str_value[:max_length] + '...'
    return str_value


def format_datetime(date_str, time_str=None):
    """날짜를 yy-mm-dd 00:00시 형식으로 변환"""
    try:
        if pd.isna(date_str) or date_str == '':
            return ''
        
        date_str = str(date_str).strip()
        
        # 20221120 1500 형식 (인터파크)
        if len(date_str) >= 13 and date_str[:8].isdigit():
            year = date_str[2:4]
            month = date_str[4:6]
            day = date_str[6:8]
            hour = date_str[9:11] if len(date_str) > 9 else '00'
            minute = date_str[11:13] if len(date_str) > 11 else '00'
            return f"{year}-{month}-{day} {hour}:{minute}시"
        
        # 2022.11.19 형식 (티켓링크)
        if '.' in date_str:
            parts = date_str.split('.')
            if len(parts) >= 3:
                year = parts[0][-2:]
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)
                
                # 시간이 별도로 있으면 추가
                if time_str and '/' in str(time_str):
                    time_part = str(time_str).split('/')[1]  # "1/14:00" -> "14:00"
                    if ':' in time_part:
                        hour, minute = time_part.split(':')
                        return f"{year}-{month}-{day} {hour.zfill(2)}:{minute.zfill(2)}시"
                
                return f"{year}-{month}-{day} 00:00시"
        
        # 2022-11-20 15:00 형식 (예스24)
        if '-' in date_str:
            # 공백으로 날짜와 시간 분리
            parts = date_str.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else None
            
            date_components = date_part.split('-')
            if len(date_components) >= 3:
                year = date_components[0][-2:]
                month = date_components[1].zfill(2)
                day = date_components[2].zfill(2)
                
                if time_part and ':' in time_part:
                    hour, minute = time_part.split(':')[:2]
                    return f"{year}-{month}-{day} {hour.zfill(2)}:{minute.zfill(2)}시"
                
                return f"{year}-{month}-{day} 00:00시"
        
        return safe_str(date_str)
    except Exception as e:
        return safe_str(date_str)


def process_interpark(df, source_name):
    """인터파크 데이터 처리 (헤더: 6행, 데이터: 7행부터)"""
    try:
        # 6행을 헤더로 사용 (인덱스 5)
        df.columns = df.iloc[5]
        df = df.iloc[6:].reset_index(drop=True)
        
        result = pd.DataFrame()
        result['예매처'] = source_name
        
        # A열: 공연일시 (20221120 1500)
        if '공연일시' in df.columns:
            result['공연일시'] = df['공연일시'].apply(lambda x: format_datetime(x))
        else:
            result['공연일시'] = ''
        
        # J열: 예매자
        if '예매자' in df.columns:
            result['예매자이름'] = df['예매자'].apply(safe_str)
        else:
            result['예매자이름'] = ''
        
        # 매수: 각 행이 1좌석
        result['매수'] = '1'
        
        # E열: 좌석정보
        if '좌석정보' in df.columns:
            result['좌석번호'] = df['좌석정보'].apply(lambda x: safe_str(x, 200))
        else:
            result['좌석번호'] = ''
        
        # K열: 전화번호
        if '전화번호' in df.columns:
            result['연락처'] = df['전화번호'].apply(lambda x: safe_str(x, 100))
        else:
            result['연락처'] = ''
        
        return result
    except Exception as e:
        st.error(f"인터파크 처리 오류: {e}")
        return pd.DataFrame()


def process_ticketlink(df, source_name):
    """티켓링크 데이터 처리 (헤더: 6행, 데이터: 7행부터)"""
    try:
        # 6행을 헤더로 사용 (인덱스 5)
        df.columns = df.iloc[5]
        df = df.iloc[6:].reset_index(drop=True)
        
        result = pd.DataFrame()
        result['예매처'] = source_name
        
        # A열: 공연일, B열: 회차/시간
        if '공연일' in df.columns and '회차/시간' in df.columns:
            result['공연일시'] = df.apply(
                lambda row: format_datetime(row['공연일'], row['회차/시간']),
                axis=1
            )
        elif '공연일' in df.columns:
            result['공연일시'] = df['공연일'].apply(lambda x: format_datetime(x))
        else:
            result['공연일시'] = ''
        
        # D열: 성명
        if '성명' in df.columns:
            result['예매자이름'] = df['성명'].apply(safe_str)
        else:
            result['예매자이름'] = ''
        
        # H열: 매수
        if '매수' in df.columns:
            result['매수'] = df['매수'].apply(lambda x: safe_str(x, 50))
        else:
            result['매수'] = ''
        
        # J열: 좌석
        if '좌석' in df.columns:
            result['좌석번호'] = df['좌석'].apply(lambda x: safe_str(x, 200))
        else:
            result['좌석번호'] = ''
        
        # E열: 연락처(SMS)
        if '연락처(SMS)' in df.columns:
            result['연락처'] = df['연락처(SMS)'].apply(lambda x: safe_str(x, 100))
        elif '연락처' in df.columns:
            result['연락처'] = df['연락처'].apply(lambda x: safe_str(x, 100))
        else:
            result['연락처'] = ''
        
        return result
    except Exception as e:
        st.error(f"티켓링크 처리 오류: {e}")
        return pd.DataFrame()


def process_yes24(df, source_name):
    """예스24 데이터 처리 (헤더: 20행, 데이터: 21행부터)"""
    try:
        # 상단에서 공연일시 추출 (대략 2-4행 사이)
        performance_datetime = ''
        for i in range(min(10, len(df))):
            for col in df.columns:
                cell_value = str(df.iloc[i][col])
                # "2022-11-20 15:00" 형식 찾기
                if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', cell_value):
                    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', cell_value)
                    if match:
                        performance_datetime = format_datetime(match.group(1))
                        break
            if performance_datetime:
                break
        
        # 20행을 헤더로 사용 (인덱스 19)
        if len(df) < 20:
            st.warning("예스24 파일이 20행보다 짧습니다.")
            return pd.DataFrame()
        
        df.columns = df.iloc[19]
        df = df.iloc[20:].reset_index(drop=True)
        
        result = pd.DataFrame()
        result['예매처'] = source_name
        
        # 공연일시는 상단에서 추출한 값 사용
        result['공연일시'] = performance_datetime if performance_datetime else ''
        
        # B열 근처: 예매자명 (병합된 열이므로 첫 번째 값 확인)
        name_col = None
        for col in df.columns:
            if '예매자' in str(col) or '이름' in str(col):
                name_col = col
                break
        
        if name_col:
            result['예매자이름'] = df[name_col].apply(safe_str)
        else:
            # B, C, D 열 중 데이터가 있는 열 찾기
            for idx in [1, 2, 3]:  # B=1, C=2, D=3
                if idx < len(df.columns):
                    col = df.columns[idx]
                    if df[col].notna().any():
                        result['예매자이름'] = df[col].apply(safe_str)
                        break
            else:
                result['예매자이름'] = ''
        
        # 매수: 각 행이 1좌석
        result['매수'] = '1'
        
        # Q열: 좌석정보
        seat_col = None
        for col in df.columns:
            if '좌석' in str(col):
                seat_col = col
                break
        
        if seat_col:
            result['좌석번호'] = df[seat_col].apply(lambda x: safe_str(x, 200))
        else:
            result['좌석번호'] = ''
        
        # E열 근처: 비상연락처
        phone_col = None
        for col in df.columns:
            if '연락처' in str(col) or '전화' in str(col):
                phone_col = col
                break
        
        if phone_col:
            result['연락처'] = df[phone_col].apply(lambda x: safe_str(x, 100))
        else:
            result['연락처'] = ''
        
        return result
    except Exception as e:
        st.error(f"예스24 처리 오류: {e}")
        return pd.DataFrame()


def detect_source_type(df, filename):
    """파일 구조를 분석하여 예매처 판단"""
    try:
        # 파일명으로 먼저 추측
        filename_lower = filename.lower()
        if 'ticket' in filename_lower or '티켓링크' in filename:
            return 'ticketlink'
        elif 'inter' in filename_lower or '인터파크' in filename:
            return 'interpark'
        elif 'yes' in filename_lower or '예스' in filename:
            return 'yes24'
        
        # 파일 내용으로 판단
        # 처음 25행 정도를 문자열로 변환해서 확인
        sample_text = ''
        for i in range(min(25, len(df))):
            for col in df.columns:
                sample_text += str(df.iloc[i][col]) + ' '
        
        sample_text = sample_text.lower()
        
        # 티켓링크 특징
        if 'ticketlink' in sample_text or '회차/시간' in sample_text:
            return 'ticketlink'
        
        # 인터파크 특징
        if 'interpark' in sample_text or '판매좌석수' in sample_text or '티켓배송' in sample_text:
            return 'interpark'
        
        # 예스24 특징
        if 'yes24' in sample_text or '비상연락처' in sample_text:
            return 'yes24'
        
        return 'unknown'
    except:
        return 'unknown'


def merge_uploaded_files(uploaded_files):
    """업로드된 파일들을 통합"""
    all_data = []
    processing_log = []
    
    for uploaded_file in uploaded_files:
        try:
            # 파일 확장자 확인
            file_ext = uploaded_file.name.split('.')[-1].lower()
            
            # 엑셀 파일 읽기
            if file_ext == 'xls':
                df = pd.read_excel(uploaded_file, engine='xlrd', header=None)
            else:
                df = pd.read_excel(uploaded_file, header=None)
            
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
            if source_type == 'interpark':
                result_df = process_interpark(df, source_name)
            elif source_type == 'ticketlink':
                result_df = process_ticketlink(df, source_name)
            elif source_type == 'yes24':
                result_df = process_yes24(df, source_name)
            else:
                processing_log[-1]['error'] = '예매처를 자동 감지할 수 없습니다'
                continue
            
            if not result_df.empty:
                all_data.append(result_df)
                processing_log[-1]['processed'] = len(result_df)
            else:
                processing_log[-1]['error'] = '처리된 데이터가 없습니다'
            
        except Exception as e:
            processing_log.append({
                'file': uploaded_file.name,
                'error': f'처리 실패: {str(e)}'
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
    - **인터파크**: 6행 헤더 형식
    - **티켓링크**: 5행 헤더 형식
    - **예스24**: 20행 헤더 형식
    
    ### 사용 방법
    1. 아래에서 엑셀 파일들을 선택하거나 드래그하세요
    2. '통합하기' 버튼을 클릭하세요
    3. 통합된 명부를 다운로드하세요!
    
    💡 **팁**: 파일명에 예매처 이름을 포함하면 더 정확합니다.
    """)

st.markdown("---")

# 파일 업로드
uploaded_files = st.file_uploader(
    "📁 엑셀 파일을 선택하세요 (여러 개 가능)",
    type=['xlsx', 'xls'],
    accept_multiple_files=True,
    help="인터파크, 티켓링크, 예스24 엑셀 파일을 모두 선택하세요"
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
        
        if merged_df is not None and not merged_df.empty:
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
            - 파일명에 예매처 이름을 포함해보세요 (예: 인터파크_공연명.xlsx)
            - 인터파크(6행), 티켓링크(5행), 예스24(20행) 헤더 형식 확인
            """)

else:
    st.info("👆 위에서 엑셀 파일을 업로드해주세요!")

# 푸터
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🎭 티켓츠(tCATS) 예매 명부 통합 시스템</p>
    <p style='font-size: 0.8em;'>인터파크 / 티켓링크 / 예스24 자동 통합</p>
</div>
""", unsafe_allow_html=True)
