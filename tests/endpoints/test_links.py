import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient) -> str:
    await client.post(
        "/auth/register", json={"username": "linkuser", "password": "pwd"}
    )
    response = await client.post(
        "/auth/login",
        data={"username": "linkuser", "password": "pwd"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def admin_auth_token(
    client: AsyncClient, db_session: AsyncSession
) -> str:
    # Register user
    await client.post(
        "/auth/register", json={"username": "adminuser", "password": "pwd"}
    )
    # Set admin=True manually in DB
    await db_session.execute(
        text("UPDATE users SET admin = True WHERE username = 'adminuser'")
    )
    await db_session.commit()

    response = await client.post(
        "/auth/login",
        data={"username": "adminuser", "password": "pwd"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_link_success(
        client: AsyncClient,
        auth_token: str
) -> None:
    response = await client.post(
        "/links",
        json={"url": "http://example.com/test"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "http://example.com/test"
    assert "short_code" in data


@pytest.mark.asyncio
async def test_create_link_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/links",
        json={"url": "http://example.com/test"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_short_code_redirect(
        client: AsyncClient,
        auth_token: str
) -> None:
    # Create link
    resp = await client.post(
        "/links",
        json={"url": "http://example.com/target"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    short_code = resp.json()["short_code"]

    # Access link (allow_redirects=False to catch the 307)
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "http://example.com/target"


@pytest.mark.asyncio
async def test_get_short_code_not_found(client: AsyncClient) -> None:
    response = await client.get("/nonexist")
    assert response.status_code == 404
    assert response.json()["detail"] == "Link not found or expired"


@pytest.mark.asyncio
async def test_get_link_stats(
    client: AsyncClient, auth_token: str, admin_auth_token: str
) -> None:
    # Create link as normal user
    resp = await client.post(
        "/links",
        json={"url": "http://example.com/stats"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    short_code = resp.json()["short_code"]

    # Click link a few times
    await client.get(f"/{short_code}", follow_redirects=False)
    await client.get(f"/{short_code}", follow_redirects=False)

    # Getting stats as normal user fails
    response = await client.get(
        f"/{short_code}/stats",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User is not admin"

    # Wait for background task to be processed
    await asyncio.sleep(0.1)

    # Getting stats as admin succeeds
    response = await client.get(
        f"/{short_code}/stats", 
        headers={"Authorization": f"Bearer {admin_auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] == 2
    assert data["last_24_hours_clicks"] == 2


@pytest.mark.asyncio
async def test_get_links_list(client: AsyncClient, auth_token: str) -> None:
    # Create multiple links
    for i in range(3):
        await client.post(
            "/links",
            json={"url": f"http://example.com/{i}"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

    response = await client.get(
        "/links?page=1&size=2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["links"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2
    assert data["page"] == 1
