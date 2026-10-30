from app.models.entities import Application

def test_deficiency_return_requires_reason(client, officer_token, db_session):
    # Find application in SCRUTINY stage
    app = db_session.query(Application).filter(
        Application.current_stage_code == "SCRUTINY",
        Application.workflow_status == "UNDER_REVIEW"
    ).first()
    assert app is not None

    # Attempt to return for deficiency without reason
    response = client.post(
        f"/api/v1/applications/{app.id}/actions",
        json={"action": "RETURN_DEFICIENCY", "reason": ""},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert response.status_code == 422
    assert "detailed reason is mandatory" in response.json()["detail"]

def test_deficiency_return_and_audit_event(client, officer_token, db_session):
    app = db_session.query(Application).filter(
        Application.current_stage_code == "SCRUTINY",
        Application.workflow_status == "UNDER_REVIEW"
    ).first()

    reason_text = "Building safety inspection certificate missing valid stamp."
    response = client.post(
        f"/api/v1/applications/{app.id}/actions",
        json={"action": "RETURN_DEFICIENCY", "reason": reason_text},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_status"] == "DEFICIENCY_RETURNED"

    # Verify audit event recorded
    history_resp = client.get(
        f"/api/v1/applications/{app.id}/history",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert history_resp.status_code == 200
    events = history_resp.json()
    assert any(e["action"] == "RETURN_DEFICIENCY" and reason_text in (e["reason"] or "") for e in events)

def test_advance_stage_flow(client, officer_token, db_session):
    app = db_session.query(Application).filter(
        Application.application_no == "APP-2026-AICTE-1001"
    ).first()
    
    # Advance to EVC
    response = client.post(
        f"/api/v1/applications/{app.id}/actions",
        json={"action": "ADVANCE", "reason": "Scrutiny completed satisfactorily."},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert response.status_code == 200
    assert response.json()["current_stage_code"] == "EVC"
    assert response.json()["workflow_status"] == "UNDER_REVIEW"
