from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_active_admin
from ...database import get_session
from ...models import FraudAlert, FraudStatus, User
from ...schemas import FraudAlertRead, FraudAlertResolve

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/fraud-alerts", response_model=list[FraudAlertRead])
async def list_fraud_alerts(
    current_user: User = Depends(get_active_admin),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(FraudAlert))
    return result.scalars().all()


@router.post("/fraud-alerts/{alert_id}/resolve", response_model=FraudAlertRead)
async def resolve_fraud_alert(
    alert_id: int,
    payload: FraudAlertResolve,
    current_user: User = Depends(get_active_admin),
    session: AsyncSession = Depends(get_session),
):
    alert = await session.get(FraudAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    alert.resolved_by = current_user.id
    await session.commit()
    await session.refresh(alert)
    return alert
