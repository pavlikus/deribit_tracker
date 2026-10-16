import logging
from decimal import Decimal
from typing import Self, Any

import aiohttp
from sqlalchemy import Select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.config import settings
from app.models import PriceTick

logger = logging.getLogger(__name__)


class DeribitClient:
    def __init__(self: Self) -> None:
        self.timeout = aiohttp.ClientTimeout()

    async def get_index_price(
        self: Self,
        session: aiohttp.ClientSession,
        ticker: str,
    ) -> float | None:
        """Fetches the index price for the specified cryptocurrency asset."""
        code_success = 200
        params = {"index_name": ticker}
        url = f"{settings.base_url}/api/v2/public/get_index_price"

        try:
            async with session.get(
                url,
                params=params,
                timeout=self.timeout,
            ) as response:
                if response.status != code_success:
                    logger.error(
                        f"Deribit API error for {ticker}:"
                        f" HTTP {response.status}"
                    )
                    return None
                data = await response.json()
                return data.get("result", {}).get("index_price")
        except Exception as e:
            logger.error(
                f"Failed to fetch price for {ticker} from Deribit: {e}"
            )
            return None


class PriceService:
    @staticmethod
    def save_price_sync(
        session: Session, ticker: str, price: Decimal, timestamp: int
    ) -> PriceTick:
        tick = PriceTick(
            ticker=ticker.lower(), price=price, timestamp=timestamp
        )
        session.add(tick)
        session.commit()
        return tick

    @staticmethod
    def _apply_ticker_filter(
        query: Select | SelectOfScalar, ticker: str
    ) -> Any:
        return query.where(PriceTick.ticker == ticker.lower())

    async def get_all_by_ticker(
        self: Self, db: AsyncSession, ticker: str
    ) -> Any:
        """Retrieves complete historical data filtered by ticker name."""
        statement = self._apply_ticker_filter(
            select(PriceTick), ticker
        ).order_by(PriceTick.timestamp.desc())  # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_latest_price(
        self: Self, db: AsyncSession, ticker: str
    ) -> Result | None:
        """Retrieves the single absolute latest price tick recorded."""
        statement = (
            self._apply_ticker_filter(select(PriceTick), ticker)
            .order_by(PriceTick.timestamp.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self: Self, db: AsyncSession, ticker: str, start_ts: int, end_ts: int
    ) -> Any:
        """Retrieves metrics bound between two specific UNIX milestones."""
        statement = (
            self._apply_ticker_filter(select(PriceTick), ticker)
            .where(PriceTick.timestamp >= start_ts)
            .where(PriceTick.timestamp <= end_ts)
            .order_by(PriceTick.timestamp.asc())  # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalars().all()
