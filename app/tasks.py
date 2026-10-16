from celery import Celery
import asyncio
import aiohttp
import time

from app.config import settings
from app.database import SyncSessionLocal
from app.services import DeribitClient, PriceService

celery_app = Celery(
    "tasks",
    broker=settings.broker_url,
    backend=settings.broker_url,
)


async def fetch_prices_async() -> tuple[dict, int]:
    """Executes concurrent non-blocking HTTP pulls across requested assets."""
    client = DeribitClient()
    current_timestamp = int(time.time())
    results = {}

    async with aiohttp.ClientSession() as session:
        # Run fetches in parallel using native event loops
        tasks = {
            ticker: client.get_index_price(session, ticker)
            for ticker in settings.tickers
        }
        for ticker, task in tasks.items():
            price = await task
            if price is not None:
                results[ticker] = price

    return results, current_timestamp


@celery_app.task(name="tasks.fetch_deribit_prices")
def fetch_deribit_prices() -> str:
    """Synchronous Celery wrapper worker running inside standard loops."""
    # Launch async event context down to synchronous worker pipelines
    prices, timestamp = asyncio.run(fetch_prices_async())

    if not prices:
        return "No prices collected due to network errors"

    # Commit fetched values via atomic transactions using standard threads
    with SyncSessionLocal() as session:
        for ticker, price in prices.items():
            PriceService.save_price_sync(session, ticker, price, timestamp)

    return (
        f"Successfully saved prices for"
        f" {list(prices.keys())} at TS {timestamp}"
    )


celery_app.conf.beat_schedule = {
    "fetch-prices-every-minute": {
        "task": "tasks.fetch_deribit_prices",
        "schedule": settings.delay,
    },
}
celery_app.conf.timezone = "UTC"
