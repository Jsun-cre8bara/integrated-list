"""
티켓츠 예매 명부 통합 웹앱 (실제 파일 구조 반영)
인터파크, 티켓링크, 예스24 자동 통합
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
from PIL import Image

# 로고 로딩 (logo.png 파일이 있는 경우)
try:
    logo = Image.open("logo.png")
    page_icon = logo
except:
    page_icon = "🎭"

# 페이지 설정
st.set_page_config(
    page_title="티켓츠 통합명부",
    page_icon=page_icon,
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
    """다양한 문자열을 'YYYY-MM-DD HH:MM' 형식으로 변환"""
    try:
        if pd.isna(date_str) or date_str == '':
            return ''

        date_str = str(date_str).strip()

        def normalize_year(year_text):
            digits = re.sub(r'[^0-9]', '', safe_str(year_text))
            if not digits:
                return ''
            if len(digits) == 2:
                return f"20{digits}"
            if len(digits) >= 4:
                return digits[-4:]
            return digits.zfill(4)

        # 20221120 1500 형식 (인터파크)
        if len(date_str) >= 13 and date_str[:8].isdigit():
            year = normalize_year(date_str[:4])
            month = date_str[4:6]
            day = date_str[6:8]
            hour = date_str[9:11] if len(date_str) > 9 else '00'
            minute = date_str[11:13] if len(date_str) > 11 else '00'
            return f"{year}-{month}-{day} {hour}:{minute}"

        # 2022.11.19 형식 (티켓링크)
        if '.' in date_str:
            parts = [p.strip() for p in date_str.split('.') if p is not None and p.strip() != '']
            if len(parts) >= 3:
                year = normalize_year(parts[0])
                month = parts[1].zfill(2)
                day = parts[2].zfill(2)

                # 시간이 별도로 있으면 추가
                if time_str and '/' in str(time_str):
                    time_part = str(time_str).split('/')[1]  # "1/14:00" -> "14:00"
                    if ':' in time_part:
                        hour, minute = time_part.split(':')
                        return f"{year}-{month}-{day} {hour.zfill(2)}:{minute.zfill(2)}"

                return f"{year}-{month}-{day} 00:00"
        
        # 2022-11-20 15:00 형식 (예스24)
        if '-' in date_str:
            # 공백으로 날짜와 시간 분리
            parts = date_str.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else None

            date_components = date_part.split('-')
            if len(date_components) >= 3:
                year = normalize_year(date_components[0])
                month = date_components[1].zfill(2)
                day = date_components[2].zfill(2)

                if time_part and ':' in time_part:
                    hour, minute = time_part.split(':')[:2]
                    return f"{year}-{month}-{day} {hour.zfill(2)}:{minute.zfill(2)}"

                return f"{year}-{month}-{day} 00:00"

        return safe_str(date_str)
    except Exception as e:
        return safe_str(date_str)


def find_column(df, keywords):
    """주어진 키워드를 포함하는 첫 번째 열 이름을 반환"""
    lowercase_keywords = [kw.lower() for kw in keywords]
    for col in df.columns:
        col_str = safe_str(col).lower()
        if any(keyword in col_str for keyword in lowercase_keywords):
            return col
    return None


def first_non_empty(series):
    """시리즈에서 첫 번째로 비어있지 않은 값을 반환"""
    if series is None:
        return ''
    for value in series:
        str_value = safe_str(value)
        if str_value:
            return str_value
    return ''


def process_interpark(df, source_name):
    """인터파크 데이터 처리 (헤더: 6행, 데이터: 7행부터)"""
    try:
        # 6행을 헤더로 사용 (인덱스 5)
        df.columns = df.iloc[5]
        df = df.iloc[6:].reset_index(drop=True)

        # 빈 행 제거
        df = df.dropna(how='all').reset_index(drop=True)

        result = pd.DataFrame()
        result['예매처'] = source_name

        performance_col = find_column(df, ['공연명', '상품명', '티켓명', '상품'])
        if performance_col:
            performance_series = df[performance_col].apply(safe_str)
            base_name = first_non_empty(performance_series) or safe_str(source_name)
            if performance_series.replace('', pd.NA).isna().all():
                result['공연명'] = base_name
            else:
                result['공연명'] = performance_series.replace('', pd.NA).fillna(base_name)
        else:
            result['공연명'] = safe_str(source_name)

        # 공연일시
        if '공연일시' in df.columns:
            result['공연날짜시간'] = df['공연일시'].apply(lambda x: format_datetime(x))
        else:
            result['공연날짜시간'] = ''

        name_col = find_column(df, ['예매자', '성명', '이름'])
        if name_col:
            result['이름'] = df[name_col].apply(safe_str)
        else:
            result['이름'] = ''

        quantity_col = find_column(df, ['매수', '수량', '예약수', '좌석수'])
        if quantity_col:
            result['매수'] = df[quantity_col].apply(lambda x: safe_str(x, 50))
        else:
            result['매수'] = '1'

        seat_col = find_column(df, ['좌석'])
        if seat_col:
            result['예약좌석번호'] = df[seat_col].apply(lambda x: safe_str(x, 200))
        else:
            result['예약좌석번호'] = ''

        phone_col = find_column(df, ['전화', '연락'])
        if phone_col:
            result['전화번호'] = df[phone_col].apply(lambda x: safe_str(x, 100))
        else:
            result['전화번호'] = ''

        result['발권여부'] = 'X'
        result['입장여부'] = 'X'

        # 필수 데이터 없는 행 제거 (이름이 비어있으면 제거)
        result = result[
            (result['이름'].notna()) &
            (result['이름'] != '') &
            (result['이름'] != 'None')
        ].reset_index(drop=True)

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
        
        # 빈 행 제거
        df = df.dropna(how='all').reset_index(drop=True)
        
        result = pd.DataFrame()
        result['예매처'] = source_name

        performance_col = find_column(df, ['공연명', '상품명', '공연'])
        if performance_col:
            performance_series = df[performance_col].apply(safe_str)
            base_name = first_non_empty(performance_series) or safe_str(source_name)
            if performance_series.replace('', pd.NA).isna().all():
                result['공연명'] = base_name
            else:
                result['공연명'] = performance_series.replace('', pd.NA).fillna(base_name)
        else:
            result['공연명'] = safe_str(source_name)

        # A열: 공연일, B열: 회차/시간
        if '공연일' in df.columns and '회차/시간' in df.columns:
            result['공연날짜시간'] = df.apply(
                lambda row: format_datetime(row['공연일'], row['회차/시간']),
                axis=1
            )
        elif '공연일' in df.columns:
            result['공연날짜시간'] = df['공연일'].apply(lambda x: format_datetime(x))
        else:
            result['공연날짜시간'] = ''

        name_col = find_column(df, ['성명', '예매자', '이름'])
        if name_col:
            result['이름'] = df[name_col].apply(safe_str)
        else:
            result['이름'] = ''

        quantity_col = find_column(df, ['매수', '수량', '좌석수'])
        if quantity_col:
            result['매수'] = df[quantity_col].apply(lambda x: safe_str(x, 50))
        else:
            result['매수'] = '1'

        seat_col = find_column(df, ['좌석'])
        if seat_col:
            result['예약좌석번호'] = df[seat_col].apply(lambda x: safe_str(x, 200))
        else:
            result['예약좌석번호'] = ''

        phone_col = find_column(df, ['연락처', '전화'])
        if phone_col:
            result['전화번호'] = df[phone_col].apply(lambda x: safe_str(x, 100))
        else:
            result['전화번호'] = ''

        result['발권여부'] = 'X'
        result['입장여부'] = 'X'

        # 필수 데이터 없는 행 제거
        result = result[
            (result['이름'].notna()) &
            (result['이름'] != '') &
            (result['이름'] != 'None')
        ].reset_index(drop=True)

        return result
    except Exception as e:
        st.error(f"티켓링크 처리 오류: {e}")
        return pd.DataFrame()


def process_yes24(df, source_name, sheet_name=''):
    """예스24 데이터 처리 (공연일시: 6행 J~V열 또는 14행 Q~T열, 헤더: 20행, 데이터: 21행부터)"""
    try:
        sheet_label = f" ({sheet_name})" if sheet_name else ""
        
        # 공연일시 찾기
        performance_datetime = ''
        
        # 1순위: 6행 J~V열(인덱스 9~21)에서 검색
        if len(df) > 5:
            row_6 = df.iloc[5]  # 6행
            start_col = 9  # J열
            end_col = 22   # V열 다음
            
            for col_idx in range(start_col, min(end_col, len(row_6))):
                cell_value = str(row_6.iloc[col_idx])
                if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', cell_value):
                    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', cell_value)
                    if match:
                        performance_datetime = format_datetime(match.group(1))
                        st.success(f"✅ 예스24{sheet_label} 6행 {chr(65+col_idx)}열에서 공연일시: {performance_datetime}")
                        break
        
        # 2순위: 14행 Q~T열(인덱스 16~19)에서 검색
        if not performance_datetime and len(df) > 13:
            row_14 = df.iloc[13]  # 14행
            start_col = 16  # Q열
            end_col = 20    # T열 다음
            
            for col_idx in range(start_col, min(end_col, len(row_14))):
                cell_value = str(row_14.iloc[col_idx])
                if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', cell_value):
                    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', cell_value)
                    if match:
                        performance_datetime = format_datetime(match.group(1))
                        st.success(f"✅ 예스24{sheet_label} 14행 {chr(65+col_idx)}열에서 공연일시: {performance_datetime}")
                        break
        
        # 3순위: 6행 전체 검색
        if not performance_datetime and len(df) > 5:
            row_6 = df.iloc[5]
            for cell_value in row_6:
                cell_str = str(cell_value)
                if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', cell_str):
                    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', cell_str)
                    if match:
                        performance_datetime = format_datetime(match.group(1))
                        st.info(f"✅ 예스24{sheet_label} 6행에서 공연일시: {performance_datetime}")
                        break
        
        # 4순위: 1~15행 전체 검색
        if not performance_datetime:
            st.warning(f"⚠️ 예스24{sheet_label} 6행, 14행에서 찾지 못해 전체 검색...")
            for i in range(min(15, len(df))):
                for col_idx in range(min(30, len(df.columns))):
                    cell_value = str(df.iloc[i, col_idx])
                    if re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', cell_value):
                        match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', cell_value)
                        if match:
                            performance_datetime = format_datetime(match.group(1))
                            st.info(f"✅ 예스24{sheet_label} {i+1}행에서 공연일시: {performance_datetime}")
                            break
                if performance_datetime:
                    break
        
        if not performance_datetime:
            st.error(f"❌ 예스24{sheet_label} 공연일시를 찾을 수 없습니다.")
        
        # 20행을 헤더로 사용
        if len(df) < 20:
            st.error(f"❌ 예스24{sheet_label} 파일이 너무 짧습니다 (총 {len(df)}행).")
            return pd.DataFrame()
        
        df.columns = df.iloc[19]
        df = df.iloc[20:].reset_index(drop=True)
        df = df.dropna(how='all').reset_index(drop=True)
        
        if len(df) == 0:
            st.warning(f"⚠️ 예스24{sheet_label} 20행 이후 데이터 없음")
            return pd.DataFrame()
        
        result = pd.DataFrame()

        # 예매처 이름: 파일명_시트명
        full_source_name = f"{source_name}_{sheet_name}" if sheet_name else source_name
        result['예매처'] = full_source_name
        result['공연날짜시간'] = performance_datetime if performance_datetime else ''

        performance_col = find_column(df, ['공연명', '상품명', '공연'])
        if performance_col:
            performance_series = df[performance_col].apply(safe_str)
            base_name = first_non_empty(performance_series) or safe_str(source_name)
            if performance_series.replace('', pd.NA).isna().all():
                result['공연명'] = base_name
            else:
                result['공연명'] = performance_series.replace('', pd.NA).fillna(base_name)
        else:
            result['공연명'] = safe_str(source_name)

        # 예매자명 찾기
        name_col = None
        for col in df.columns:
            col_str = str(col).strip()
            if col_str == '예매자명' or '예매자' in col_str or '이름' in col_str or '성명' in col_str:
                name_col = col
                break

        if name_col:
            result['이름'] = df[name_col].apply(safe_str)
        else:
            found = False
            for idx in range(min(10, len(df.columns))):
                col = df.columns[idx]
                if df[col].notna().any():
                    sample = df[col].dropna().head(3).astype(str)
                    if len(sample) > 0 and all(2 <= len(s.strip()) <= 10 for s in sample if s.strip()):
                        result['이름'] = df[col].apply(safe_str)
                        found = True
                        break
            if not found:
                result['이름'] = ''

        seat_count_col = find_column(df, ['매수', '수량', '좌석수', '인원'])
        if seat_count_col:
            result['매수'] = df[seat_count_col].apply(lambda x: safe_str(x, 50))
        elif len(df.columns) > 16:
            fallback_col = df.columns[16]
            result['매수'] = df[fallback_col].apply(lambda x: safe_str(x, 50))
        else:
            result['매수'] = '1'

        # 좌석정보
        seat_col = find_column(df, ['좌석'])
        if seat_col:
            result['예약좌석번호'] = df[seat_col].apply(lambda x: safe_str(x, 200))
        else:
            result['예약좌석번호'] = ''

        # 연락처
        phone_col = find_column(df, ['연락처', '전화'])
        if phone_col:
            result['전화번호'] = df[phone_col].apply(lambda x: safe_str(x, 100))
        else:
            result['전화번호'] = ''

        result['발권여부'] = 'X'
        result['입장여부'] = 'X'

        # 필수 데이터 없는 행 제거
        result = result[
            (result['이름'].notna()) &
            (result['이름'] != '') &
            (result['이름'] != 'None')
        ].reset_index(drop=True)

        if len(result) > 0:
            st.success(f"✅ 예스24{sheet_label} 처리 완료: {len(result)}건")

        return result
    except Exception as e:
        st.error(f"❌ 예스24{sheet_label} 처리 오류: {e}")
        import traceback
        st.code(traceback.format_exc())
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


def read_excel_with_fallback(file_bytes, file_ext, **kwargs):
    """xlrd 미설치 등으로 인한 ValueError를 사용자 친화적으로 처리"""
    buffer = io.BytesIO(file_bytes)
    if file_ext == 'xls':
        kwargs.setdefault('engine', 'xlrd')
    try:
        return pd.read_excel(buffer, **kwargs)
    except ImportError as exc:
        raise RuntimeError("xlrd 패키지가 설치되어야 합니다. 'pip install xlrd==2.0.1' 명령으로 설치해주세요.") from exc
    except ValueError as exc:
        message = str(exc)
        if 'xlrd' in message.lower():
            raise RuntimeError("xlrd 패키지가 없어 .xls 파일을 열 수 없습니다. 'pip install xlrd==2.0.1' 설치 후 다시 시도해주세요.") from exc
        raise


def merge_uploaded_files(uploaded_files):
    """업로드된 파일들을 통합"""
    all_data = []
    processing_log = []
    
    for uploaded_file in uploaded_files:
        try:
            # 파일 확장자 확인
            file_ext = uploaded_file.name.split('.')[-1].lower()
            file_bytes = uploaded_file.getvalue()

            # 감지용 데이터프레임 로드
            df_for_detection = read_excel_with_fallback(file_bytes, file_ext, header=None)

            # 파일명 (확장자 제외)
            source_name = uploaded_file.name.rsplit('.', 1)[0]

            # 예매처 타입 자동 감지
            source_type = detect_source_type(df_for_detection, uploaded_file.name)

            processing_log.append({
                'file': uploaded_file.name,
                'rows': len(df_for_detection),
                'type': source_type
            })

            # 예매처별 처리
            if source_type == 'interpark':
                df = read_excel_with_fallback(file_bytes, file_ext, header=None)
                result_df = process_interpark(df, source_name)
            elif source_type == 'ticketlink':
                df = read_excel_with_fallback(file_bytes, file_ext, header=None)
                result_df = process_ticketlink(df, source_name)
            elif source_type == 'yes24':
                sheet_results = []
                read_kwargs = {'sheet_name': None, 'header': None}
                sheets = read_excel_with_fallback(file_bytes, file_ext, **read_kwargs)
                for sheet_name, sheet_df in sheets.items():
                    if sheet_df is None or sheet_df.dropna(how='all').empty:
                        continue
                    sheet_result = process_yes24(sheet_df, source_name, sheet_name)
                    if not sheet_result.empty:
                        sheet_results.append(sheet_result)
                if sheet_results:
                    result_df = pd.concat(sheet_results, ignore_index=True)
                else:
                    result_df = pd.DataFrame()
            else:
                processing_log[-1]['error'] = '예매처를 자동 감지할 수 없습니다'
                continue
            
            if not result_df.empty:
                all_data.append(result_df)
                processing_log[-1]['processed'] = len(result_df)
            else:
                processing_log[-1]['error'] = '처리된 데이터가 없습니다'
            
        except RuntimeError as e:
            processing_log.append({
                'file': uploaded_file.name,
                'error': str(e)
            })
        except Exception as e:
            processing_log.append({
                'file': uploaded_file.name,
                'error': f'처리 실패: {str(e)}'
            })
    
    if not all_data:
        return None, processing_log
    
    # 모든 데이터 합치기
    merged_df = pd.concat(all_data, ignore_index=True)

    # 컬럼 순서 정리 및 누락값 보정
    final_columns = [
        '공연명',
        '공연날짜시간',
        '예매처',
        '이름',
        '전화번호',
        '매수',
        '예약좌석번호',
        '발권여부',
        '입장여부'
    ]

    for column in final_columns:
        if column not in merged_df.columns:
            merged_df[column] = ''

    merged_df = merged_df[final_columns]

    merged_df['발권여부'] = merged_df['발권여부'].replace('', 'X').fillna('X')
    merged_df['입장여부'] = merged_df['입장여부'].replace('', 'X').fillna('X')

    return merged_df, processing_log


# 메인 UI
# 로고와 제목
col1, col2 = st.columns([1, 10])
with col1:
    try:
        st.image("logo.png", width=80)
    except:
        st.markdown("# 🎭")
with col2:
    st.title("티켓츠 예매 명부 통합")

st.markdown("---")

# 안내 메시지
with st.expander("📖 사용 방법", expanded=True):
    st.markdown("""
    ### 지원 예매처
    - **인터파크**: 6행 헤더 형식
    - **티켓링크**: 6행 헤더 형식
    - **예스24**: 20행 헤더 형식
    
    ### 사용 방법
    1. 아래에서 엑셀 파일들을 선택하거나 드래그하세요
    2. '통합하기' 버튼을 클릭하세요
    3. 통합된 명부를 다운로드하세요!
    
    💡 **팁**: 파일명에 예매처 이름을 포함하면 더 정확합니다.
    
    ### ✨ 자동 처리 기능
    - 빈 행 자동 제거
    - 불완전한 데이터 자동 필터링
    - 예매처별 형식 자동 인식
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
    <p>🎭 티켓츠(tCATS) 예매 명부 통합 시스템 v2.0</p>
    <p style='font-size: 0.8em;'>인터파크(6행) / 티켓링크(6행) / 예스24(20행) 자동 통합</p>
    <p style='font-size: 0.8em;'>빈 행 자동 제거 · 데이터 검증 기능 포함</p>
</div>
""", unsafe_allow_html=True)
