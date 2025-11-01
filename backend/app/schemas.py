from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    role: str = "user"


class UserRead(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PerformanceRead(BaseModel):
    id: int
    title: str
    venue: Optional[str]
    start_at: datetime
    end_at: Optional[datetime]

    class Config:
        from_attributes = True


class StampBase(BaseModel):
    merchant_id: int
    discount_amount: Optional[float] = None
    approval_method: Optional[str] = None
    photo_url: Optional[str] = None


class StampCreate(StampBase):
    qr_token_id: Optional[int] = None


class StampRead(StampBase):
    id: int
    stamp_book_id: int
    status: str
    visit_at: datetime

    class Config:
        from_attributes = True


class StampBookBase(BaseModel):
    performance_id: int
    expires_at: Optional[datetime] = None


class StampBookCreate(StampBookBase):
    pass


class StampBookRead(StampBookBase):
    id: int
    user_id: int
    issued_at: datetime
    status: str
    stamps: List[StampRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class MerchantRead(BaseModel):
    id: int
    name: str
    category: Optional[str]
    address: Optional[str]
    status: str

    class Config:
        from_attributes = True


class FraudAlertRead(BaseModel):
    id: int
    stamp_id: int
    reason: str
    score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FraudAlertResolve(BaseModel):
    status: str = Field(pattern="^(reviewing|resolved)$")


class AuditLogRead(BaseModel):
    id: int
    actor_id: int
    actor_role: str
    action: str
    target_type: str
    target_id: Optional[int]
    metadata_json: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
