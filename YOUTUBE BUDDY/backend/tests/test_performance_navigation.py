"""Regression tests for post-login navigation performance and cache behavior."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.cache import get_cache, set_cache, delete_cache


from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session


@pytest.mark.asyncio
async def test_cache_fallback_operations():
    """Verify in-memory / Redis cache set, get, and delete operations."""
    test_key = "test:regression:perf"
    test_value = {"user_id": 999, "role": "creator", "plan": "pro"}

    await set_cache(test_key, test_value, expire=60)
    cached = await get_cache(test_key)
    assert cached == test_value

    await delete_cache(test_key)
    deleted = await get_cache(test_key)
    assert deleted is None


@pytest.mark.asyncio
async def test_post_login_navigation_caching(engine):
    """Verify that user profile and analytics overview are cached after the initial request."""
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():
        async with async_session_maker() as sess:
            yield sess

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Login to get token
            login_res = await client.post("/api/v1/auth/dev-login")
            assert login_res.status_code == 200
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 2. First call to profile (populates cache)
            p1 = await client.get("/api/v1/user/profile", headers=headers)
            assert p1.status_code == 200
            uid = p1.json()["uid"]

            # Cache key should now exist
            cached_profile = await get_cache(f"user_profile:{uid}")
            assert cached_profile is not None
            assert cached_profile["uid"] == uid

            # 3. Subsequent call should return fast matching payload
            p2 = await client.get("/api/v1/user/profile", headers=headers)
            assert p2.status_code == 200
            assert p2.json()["uid"] == uid

            # 4. Analytics overview endpoint caching
            o1 = await client.get("/api/v1/analytics/overview", headers=headers)
            assert o1.status_code == 200
            o1_data = o1.json()

            o2 = await client.get("/api/v1/analytics/overview", headers=headers)
            assert o2.status_code == 200
            assert o2.json() == o1_data
    finally:
        app.dependency_overrides.clear()
