from app.services.sla_engine import SLAEngine

def test_sla_evaluation_idempotency(db_session, client, officer_token):
    # First execution creates alerts for seeded overdue cases
    total_eval, new_created, details = SLAEngine.evaluate_all(db_session)
    assert total_eval > 0

    # Running immediately a second time must create ZERO duplicate alerts
    total_eval2, new_created2, details2 = SLAEngine.evaluate_all(db_session)
    assert new_created2 == 0

def test_api_deadline_check_endpoint(client, officer_token):
    response = client.post(
        "/api/v1/alerts/check",
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_evaluated" in data
    assert "new_alerts_created" in data
