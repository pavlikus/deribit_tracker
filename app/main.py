from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import Any, Annotated

from fastapi import FastAPI, Query, Depends, HTTPException, status
from sqlalchemy import Result
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import init_db, get_async_db
from app.models import PriceTick
from app.services import PriceService


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # ruff: ignore[ARG001]
    await init_db()
    yield


app = FastAPI(debug=settings.debug, lifespan=lifespan)
price_service = PriceService()

DatabaseSession = Annotated[AsyncSession, Depends(get_async_db)]


@app.get("/prices", response_model=list[PriceTick])
async def get_all_prices(
    ticker: str = Query(
        ..., description="Target currency code (e.g., 'btc_usd')"
    ),
    db: DatabaseSession = None,
) -> list[PriceTick]:
    """Retrieves all stored timeline price entries filtered by ticker."""
    return await price_service.get_all_by_ticker(db, ticker)


@app.get("/prices/latest", response_model=PriceTick)
async def get_latest_price(
    ticker: str = Query(
        ..., description="Target currency code (e.g., 'btc_usd')"
    ),
    db: DatabaseSession = None,
) -> Result:
    """Retrieves the single absolute latest price point available."""
    tick = await price_service.get_latest_price(db, ticker)
    if not tick:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tracked data found for ticker '{ticker}'",
        )
    return tick


@app.get("/prices/filter", response_model=list[PriceTick])
async def get_prices_by_date(
    ticker: str = Query(..., description="Target currency code"),
    start_date: str = Query(
        ..., description="Start date bounds in YYYY-MM-DD format"
    ),
    end_date: str = Query(
        ..., description="End date bounds in YYYY-MM-DD format"
    ),
    db: DatabaseSession = None,
) -> Result[PriceTick, None]:
    """Filters database price records across custom timeframes."""
    try:
        # Resolve user dates strictly into UTC UNIX epochs
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
            tzinfo=UTC
        )
        start_ts = int(start_dt.timestamp())

        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=UTC
        )
        end_ts = int(end_dt.timestamp())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid datetime parsing pattern. "
                "Utilize exact YYYY-MM-DD parameters."
            ),
        ) from None

    if start_ts > end_ts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Target start_date configuration "
                "cannot cross beyond end_date parameter milestones."
            ),
        ) from None

    return await price_service.get_by_date_range(db, ticker, start_ts, end_ts)
