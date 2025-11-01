from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog


async def record_audit_log(
    session: AsyncSession,
    *,
    actor_id: int,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    metadata_json: Optional[str] = None,
) -> None:
    log = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata_json,
        created_at=datetime.utcnow(),
    )
    session.add(log)
    await session.flush()
