import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_success(
        client: AsyncClient,
        db_session: AsyncSession
) -> None:
    response = await client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_register_duplicate(
        client: AsyncClient,
        db_session: AsyncSession
) -> None:
    await client.post(
        "/auth/register",
        json={"username": "testuser2", "password": "testpassword"}
    )
    # Second time should fail
    response = await client.post(
        "/auth/register",
        json={"username": "testuser2", "password": "testpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


@pytest.mark.asyncio
async def test_login_success(
        client: AsyncClient,
        db_session: AsyncSession
) -> None:
    # Register first
    await client.post(
        "/auth/register",
        json={"username": "testuser3", "password": "testpassword"}
    )

    # Login
    response = await client.post(
        "/auth/login",
        data={"username": "testuser3", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(
        client: AsyncClient,
        db_session: AsyncSession
) -> None:
    await client.post(
        "/auth/register",
        json={"username": "testuser4", "password": "testpassword"}
    )

    response = await client.post(
        "/auth/login",
        data={"username": "testuser4", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_login_invalid_username(
        client: AsyncClient,
        db_session: AsyncSession
) -> None:
    response = await client.post(
        "/auth/login",
        data={"username": "nonexistent", "password": "testpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
