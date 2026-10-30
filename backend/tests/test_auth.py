def test_login_success(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "officer.north@aicte.gov.in",
        "password": "Admin@AICTE2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "officer.north@aicte.gov.in"
    assert data["user"]["role"] == "REGIONAL_OFFICER"

def test_login_invalid_password(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "officer.north@aicte.gov.in",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_me_authenticated(client, officer_token):
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {officer_token}"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "officer.north@aicte.gov.in"

def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
