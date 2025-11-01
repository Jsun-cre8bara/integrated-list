# integrated-list

티켓츠 예매 명부 통합 도구와 함께 사용할 수 있는 **티켓츠 스탬프 네트워크 API** 샘플 구현입니다.  
Streamlit 기반의 프런트엔드(`app.py`)와 FastAPI + PostgreSQL(또는 SQLite) 백엔드(`backend/app`)가 함께 포함되어 있습니다.

## FastAPI 백엔드 실행 방법

```
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///./tcats.db"  # 또는 PostgreSQL URL
uvicorn backend.app.main:app --reload
```

## 주요 API 라우트

- `POST /api/auth/register`, `POST /api/auth/token`
- `GET/POST /api/stamp-books`
- `POST /api/stamp-books/{id}/stamps`
- `GET /api/merchant/stamps/pending`, `POST /api/merchant/stamps/{id}/approve`
- `GET /api/admin/fraud-alerts`, `POST /api/admin/fraud-alerts/{id}/resolve`

최초 실행 시 자동으로 스키마가 생성되며, `DATABASE_URL`을 PostgreSQL로 지정하면 실서비스 구조에 맞춰 확장할 수 있습니다.
