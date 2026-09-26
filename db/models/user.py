from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .balance import Balance
    from .income import IncomeRegular, IncomeIrregular
    from .expense import ExpenseRegular, ExpenseIrregular
    from .goal import Goal
    from .ai_log import AIQueryLog


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    plan: Mapped[str] = mapped_column(String(10), default="free")  # free | premium

    balance: Mapped["Balance"] = relationship(back_populates="user", uselist=False)
    income_regular: Mapped[list["IncomeRegular"]] = relationship(back_populates="user")
    income_irregular: Mapped[list["IncomeIrregular"]] = relationship(back_populates="user")
    expenses_regular: Mapped[list["ExpenseRegular"]] = relationship(back_populates="user")
    expenses_irregular: Mapped[list["ExpenseIrregular"]] = relationship(back_populates="user")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user")
    ai_logs: Mapped[list["AIQueryLog"]] = relationship(back_populates="user")
