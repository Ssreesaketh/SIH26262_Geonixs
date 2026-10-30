from app.models.entities import Application, Institution

def test_unauthenticated_requests_denied(client):
    assert client.get("/api/v1/applications").status_code == 401
    assert client.get("/api/v1/compliance").status_code == 401
    assert client.get("/api/v1/documents").status_code == 401
    assert client.get("/api/v1/alerts").status_code == 401

def test_institution_boundary_isolation(client, institution_token, db_session):
    # principal@zenith.edu.in belongs to Zenith (ZEN-801)
    # Find application belonging to NIT-402
    nit_inst = db_session.query(Institution).filter(Institution.institution_code == "NIT-402").first()
    nit_app = db_session.query(Application).filter(Application.institution_id == nit_inst.id).first()
    assert nit_app is not None

    # Zenith user tries to view NIT application
    response = client.get(
        f"/api/v1/applications/{nit_app.id}",
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert response.status_code == 403
    assert "belonging to another institution" in response.json()["detail"]

def test_dashboard_summary_scope(client, institution_token, officer_token):
    # Both queries succeed with their respective scoped data
    inst_resp = client.get("/api/v1/dashboard/summary", headers={"Authorization": f"Bearer {institution_token}"})
    assert inst_resp.status_code == 200

    officer_resp = client.get("/api/v1/dashboard/summary", headers={"Authorization": f"Bearer {officer_token}"})
    assert officer_resp.status_code == 200

def test_institution_cannot_view_or_acknowledge_other_institution_alert(client, institution_token, db_session):
    from app.models.entities import Notification
    nit_inst = db_session.query(Institution).filter(Institution.institution_code == "NIT-402").first()
    nit_app = db_session.query(Application).filter(Application.institution_id == nit_inst.id).first()
    alert = Notification(
        application_id=nit_app.id,
        recipient_role="INSTITUTION_USER",
        notification_type="TEST_SCOPE",
        severity="WARNING",
        message="Synthetic cross-institution scope test",
        deduplication_key=f"TEST:SCOPE:{nit_app.id}",
        status="UNREAD",
    )
    db_session.add(alert)
    db_session.commit()
    headers = {"Authorization": f"Bearer {institution_token}"}
    listing = client.get("/api/v1/alerts", headers=headers)
    assert listing.status_code == 200
    assert all(item["id"] != alert.id for item in listing.json())
    response = client.post(f"/api/v1/alerts/{alert.id}/acknowledge", headers=headers)
    assert response.status_code == 403
    resolve_response = client.post(f"/api/v1/alerts/{alert.id}/resolve", headers=headers)
    assert resolve_response.status_code == 403
