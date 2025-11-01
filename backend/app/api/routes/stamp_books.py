from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.deps import get_current_user
from ...database import get_session
from ...models import Merchant, Performance, Stamp, StampBook, User
from ...schemas import StampBookCreate, StampBookRead, StampCreate, StampRead
from ...utils.audit import record_audit_log

router = APIRouter(prefix="/stamp-books", tags=["stamp-books"])


@router.get("/", response_model=list[StampBookRead])
async def list_stamp_books(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(StampBook).where(StampBook.user_id == current_user.id)
    )
    stamp_books = result.scalars().unique().all()
    for sb in stamp_books:
        await session.refresh(sb, attribute_names=["stamps"])
    return stamp_books


@router.post("/", response_model=StampBookRead, status_code=status.HTTP_201_CREATED)
async def issue_stamp_book(
    stamp_book_in: StampBookCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    performance = await session.get(Performance, stamp_book_in.performance_id)
    if not performance:
        raise HTTPException(status_code=404, detail="Performance not found")

    existing = await session.execute(
        select(StampBook).where(
            StampBook.user_id == current_user.id,
            StampBook.performance_id == stamp_book_in.performance_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Stamp book already issued")

    stamp_book = StampBook(
        user_id=current_user.id,
        performance_id=stamp_book_in.performance_id,
        expires_at=stamp_book_in.expires_at,
    )
    session.add(stamp_book)
    await session.flush()
    await record_audit_log(
        session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="stamp_book_issued",
        target_type="stamp_book",
        target_id=stamp_book.id,
    )
    await session.commit()
    await session.refresh(stamp_book)
    return stamp_book


@router.post("/{stamp_book_id}/stamps", response_model=StampRead, status_code=status.HTTP_201_CREATED)
async def add_stamp_to_book(
    stamp_book_id: int,
    stamp_in: StampCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stamp_book = await session.get(StampBook, stamp_book_id)
    if not stamp_book or stamp_book.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Stamp book not found")

    merchant = await session.get(Merchant, stamp_in.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    stamp = Stamp(
        stamp_book_id=stamp_book_id,
        merchant_id=stamp_in.merchant_id,
        qr_token_id=stamp_in.qr_token_id,
        discount_amount=stamp_in.discount_amount,
        approval_method=stamp_in.approval_method,
        photo_url=stamp_in.photo_url,
        visit_at=datetime.utcnow(),
    )
    session.add(stamp)
    await record_audit_log(
        session,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="stamp_created",
        target_type="stamp",
        target_id=stamp.id,
    )
    await session.commit()
    await session.refresh(stamp)
    return stamp
