import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    r = await client.post(
        "/auth/register", json={"email": "test@example.com", "password": "strongpass1"}
    )
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "strongpass1"}
    await client.post("/auth/register", json=payload)
    r = await client.post("/auth/register", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_case_insensitive(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "Case@Example.com", "password": "strongpass1"}
    )
    r = await client.post(
        "/auth/register", json={"email": "case@example.com", "password": "strongpass1"}
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    r = await client.post(
        "/auth/register", json={"email": "x@example.com", "password": "123"}
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "login@example.com", "password": "strongpass1"}
    )
    r = await client.post(
        "/auth/login", json={"email": "login@example.com", "password": "strongpass1"}
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "wp@example.com", "password": "strongpass1"}
    )
    r = await client.post(
        "/auth/login", json={"email": "wp@example.com", "password": "wrongpass"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "me@example.com", "password": "strongpass1"}
    )
    login = await client.post(
        "/auth/login", json={"email": "me@example.com", "password": "strongpass1"}
    )
    token = login.json()["access_token"]

    r = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    reg = await client.post(
        "/auth/register", json={"email": "ref@example.com", "password": "strongpass1"}
    )
    refresh_token = reg.json()["refresh_token"]

    r = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["refresh_token"] != refresh_token  # токен ротирован


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    reg = await client.post(
        "/auth/register", json={"email": "out@example.com", "password": "strongpass1"}
    )
    tokens = reg.json()

    r = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r.status_code == 204

    # после logout refresh не работает
    r2 = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r2.status_code == 401


@pytest.mark.asyncio
async def test_change_password_rotates_other_sessions(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"email": "pwchange@example.com", "password": "strongpass1"},
    )
    old_refresh = reg.json()["refresh_token"]

    login = await client.post(
        "/auth/login", json={"email": "pwchange@example.com", "password": "strongpass1"}
    )
    new_tokens = login.json()
    access_token = new_tokens["access_token"]
    active_refresh = new_tokens["refresh_token"]

    change = await client.post(
        "/auth/change-password",
        json={
            "old_password": "strongpass1",
            "new_password": "newstrong2",
            "refresh_token": active_refresh,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert change.status_code == 204

    # Old session should be revoked.
    old_refresh_attempt = await client.post(
        "/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert old_refresh_attempt.status_code == 401

    # Current session refresh token should stay valid.
    active_refresh_attempt = await client.post(
        "/auth/refresh", json={"refresh_token": active_refresh}
    )
    assert active_refresh_attempt.status_code == 200

    # Login with old password must fail, new password should work.
    bad_login = await client.post(
        "/auth/login", json={"email": "pwchange@example.com", "password": "strongpass1"}
    )
    assert bad_login.status_code == 401

    good_login = await client.post(
        "/auth/login", json={"email": "pwchange@example.com", "password": "newstrong2"}
    )
    assert good_login.status_code == 200
