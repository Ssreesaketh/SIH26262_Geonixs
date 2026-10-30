from app.models.entities import Undertaking, User

def test_undertaking_submission_and_verification(client, institution_token, officer_token, db_session):
    # Find user's institution
    user = db_session.query(User).filter(User.email == "principal@zenith.edu.in").first()
    # Find pending undertaking for this institution
    und = db_session.query(Undertaking).filter(
        Undertaking.institution_id == user.institution_id,
        Undertaking.status == "PENDING"
    ).first()
    assert und is not None

    # 1. Institution submits evidence
    evidence_text = "Uploaded purchase orders for 30 GPU workstations."
    sub_resp = client.post(
        f"/api/v1/compliance/{und.id}/submit",
        json={"evidence_summary": evidence_text},
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "SUBMITTED"

    # 2. Institution attempts to verify own undertaking (MUST BE FORBIDDEN)
    verify_denied = client.post(
        f"/api/v1/compliance/{und.id}/verify",
        json={"approved": True, "verification_remarks": "Self-approved."},
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert verify_denied.status_code == 403

    # 3. Regional Officer verifies undertaking
    verify_resp = client.post(
        f"/api/v1/compliance/{und.id}/verify",
        json={"approved": True, "verification_remarks": "Invoices and equipment serial numbers verified."},
        headers={"Authorization": f"Bearer {officer_token}"}
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "VERIFIED"
    assert verify_resp.json()["verification_remarks"] == "Invoices and equipment serial numbers verified."
