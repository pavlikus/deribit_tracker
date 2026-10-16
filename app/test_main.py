import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import SQLModel


from app.main import app, price_service
from app.database import get_async_db, async_engine


# Setup the isolated async session factory for testing
TestSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    """Handles automated execution of mock db migration scripts per unique execution pass."""
    async with async_engine.begin() as conn:
        # Create all tables inside the SQLite in-memory instance
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Manages active test sessions."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def override_database(test_db_session):
    """Mutates global runtime dependencies, replacing Postgres nodes with SQLite nodes on the fly."""

    async def _get_test_db():
        yield test_db_session

    app.dependency_overrides[get_async_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    """Bootstraps isolated test clients."""
    with TestClient(app) as c:
        yield c


def test_get_prices_validation_error(client):
    """Ensures ТЗ Requirement #1 is fully locked: ticker parameters must be non-nullable."""
    response = client.get("/prices")
    assert response.status_code == 422

    # Extract the payload dictionary
    payload = response.json()

    # Ensure 'detail' is present and is a list
    assert "detail" in payload
    assert isinstance(payload["detail"], list)

    # Extract the first error block and verify the missing location field
    # Payload format: {"detail": [{"type": "missing", "loc": ["query", "ticker"], "msg": "Field required"}]}
    error_loc = payload["detail"][0]["loc"]

    # Assert that 'ticker' is indeed the missing query parameter
    assert "ticker" in error_loc


def test_get_all_prices_empty_and_filled(client, test_db_session):
    response = client.get("/prices?ticker=btc_usd")
    assert response.status_code == 200
    assert response.json() == []

    price_service.save_price_sync(
        test_db_session, "btc_usd", 65000.0, 1718400000
    )
    price_service.save_price_sync(
        test_db_session, "btc_usd", 66000.0, 1718400060
    )

    response = client.get("/prices?ticker=btc_usd")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert float(data[0]["price"]) == 66000.0


def test_get_latest_price(client, test_db_session):
    """Ensures fallback 404 controls function alongside active head-record selectors."""
    response = client.get("/prices/latest?ticker=eth_usd")
    assert response.status_code == 404

    price_service.save_price_sync(
        test_db_session, "eth_usd", 3400.0, 1718400000
    )
    price_service.save_price_sync(
        test_db_session, "eth_usd", 3500.0, 1718400100
    )

    response = client.get("/prices/latest?ticker=eth_usd")
    assert response.status_code == 200
    assert float(response.json()["price"]) == 3500.0


def test_get_prices_by_date_filter(client, test_db_session):
    """Validates bounds filtering operations inside custom timeframes."""
    price_service.save_price_sync(
        test_db_session, "btc_usd", 70000.0, 1792022400
    )
    price_service.save_price_sync(
        test_db_session, "btc_usd", 50000.0, 1500000000
    )

    response = client.get(
        "/prices/filter?ticker=btc_usd&start_date=2026-10-15&end_date=2026-10-15"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert float(data[0]["price"]) == 70000.0
