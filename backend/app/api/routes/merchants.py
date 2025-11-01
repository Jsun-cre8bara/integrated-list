from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_active_merchant
from ...database import get_session
from ...models import Merchant, Stamp, StampStatus, User
from ...schemas import StampRead
from ...utils.audit import record_audit_log

router = APIRouter(prefix="/merchant", tags=["merchant"])


@router.get("/stamps/pending", response_model=list[StampRead])
async def list_pending_stamps(
    current_user: User = Depends(get_active_merchant),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Stamp)
        .join(Merchant, Stamp.merchant_id == Merchant.id)
        .where(Merchant.owner_id == current_user.id, Stamp.status == StampStatus.PENDING.value)
    )
    stamps = result.scalars().all()
    return stamps


@router.post("/stamps/{stamp_id}/approve", response_model=StampRead)
async def approve_stamp(
    stamp_id: int,
    current_user: User = Depends(get_active_merchant),
    session: AsyncSession = Depends(get_session),
):
    stamp = await session.get(Stamp, stamp_id)
    if not stamp:
        raise HTTPException(status_code=404, detail="Stamp not found")

    merchant = await session.get(Merchant, stamp.merchant_id)
    if not merchant or merchant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this stamp")

    stamp.status = StampStatus.APPROVED.value
    stamp.visit_at = datetime.utcnow()
    await record_audit_log(
        session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="stamp_approved",
        target_type="stamp",
        target_id=stamp.id,
    )
    await session.commit()
    await session.refresh(stamp)
    return stamp
