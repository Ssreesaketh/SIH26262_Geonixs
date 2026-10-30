def test_admin_rule_update_creates_new_version(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    workflows = client.get("/api/v1/config/workflows", headers=headers)
    assert workflows.status_code == 200
    original = next(w for w in workflows.json() if w["code"] == "SCRUTINY_EVC")
    config = dict(original["configuration"])
    config["warning_threshold_percent"] = 75
    response = client.patch(f"/api/v1/config/workflows/{original['id']}", headers=headers, json={"configuration": config})
    assert response.status_code == 200, response.text
    assert response.json()["version"] == original["version"] + 1
    assert response.json()["configuration"]["warning_threshold_percent"] == 75
    versions = client.get("/api/v1/config/workflows/SCRUTINY_EVC/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()) >= 2


def test_invalid_warning_threshold_is_rejected(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    original = next(w for w in client.get("/api/v1/config/workflows", headers=headers).json() if w["code"] == "SCRUTINY_EVC")
    config = dict(original["configuration"])
    config["warning_threshold_percent"] = 100
    response = client.patch(f"/api/v1/config/workflows/{original['id']}", headers=headers, json={"configuration": config})
    assert response.status_code == 422
