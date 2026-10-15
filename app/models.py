from decimal import Decimal

from sqlmodel import Field, SQLModel


class PriceTick(SQLModel, table=True):  # type: ignore[call-arg]
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(nullable=False, max_length=20, index=True)
    price: Decimal = Field(default=0, max_digits=16, decimal_places=2)
    timestamp: int = Field(nullable=False, index=True)
