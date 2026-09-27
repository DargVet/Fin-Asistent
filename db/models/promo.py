from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization: Mapped[str] = mapped_column(String(150), nullable=False)
    purpose: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    advertiser: Mapped[str | None] = mapped_column(String(200), nullable=True)
    erid: Mapped[str | None] = mapped_column(String(100), nullable=True)
