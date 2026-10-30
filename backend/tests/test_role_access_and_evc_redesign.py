from datetime import datetime, timezone, timedelta

from app.models.entities import Application, Institution, User
from app.core.security import create_access_token


def _token(user):
    return create_access_token(
        subject=user.id,
        extra_claims={
            "role": user.role,
            "region_id": user.region_id,
            "institution_id": user.institution_id,
            "display_name": user.display_name,
        },
    )


def test_seeded_demo_has_three_institutions_three_officers_and_five_cases(db_session):
    assert db_session.query(Institution).count() == 3
    users = db_session.query(User).all()
    assert len(users) == 6
    assert sum(u.role == "INSTITUTION_USER" for u in users) == 3
    assert sum(u.role in {"REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"} for u in users) == 3
    assert db_session.query(Application).count() == 5


def test_officers_share_five_case_registry_but_institution_is_tenant_scoped(
    client, officer_token, institution_token, db_session
):
    officer_response = client.get(
        "/api/v1/applications?page_size=100",
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert officer_response.status_code == 200
    assert officer_response.json()["total"] == 5

    institution_response = client.get(
        "/api/v1/applications?page_size=100",
        headers={"Authorization": f"Bearer {institution_token}"},
    )
    assert institution_response.status_code == 200
    zenith = db_session.query(Institution).filter_by(institution_code="ZEN-801").first()
    assert all(row["institution_id"] == zenith.id for row in institution_response.json()["items"])
    assert len(institution_response.json()["items"]) == 2
    assert all(row["assigned_role"] == "UNDER_PROCESS" for row in institution_response.json()["items"])


def test_forms_are_role_scoped_and_downloadable(client, institution_token, officer_token):
    institution_headers = {"Authorization": f"Bearer {institution_token}"}
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    institution_forms = client.get("/api/v1/documents/forms", headers=institution_headers)
    assert institution_forms.status_code == 200
    institution_keys = {item["key"] for item in institution_forms.json()}
    assert institution_keys == {"institution-application-checklist", "institution-information-form"}

    officer_forms = client.get("/api/v1/documents/forms", headers=officer_headers)
    assert officer_forms.status_code == 200
    officer_keys = {item["key"] for item in officer_forms.json()}
    assert "evc-inspection-report" in officer_keys
    assert "bureau-review-checklist" not in officer_keys

    denied = client.get(
        "/api/v1/documents/forms/evc-inspection-report/download",
        headers=institution_headers,
    )
    assert denied.status_code == 403

    downloaded = client.get(
        "/api/v1/documents/forms/institution-application-checklist/download",
        headers=institution_headers,
    )
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("application/pdf")
    assert downloaded.content.startswith(b"%PDF")


def test_evc_completion_routes_to_bureau_then_final_authority_completes(
    client, officer_token, db_session
):
    app = db_session.query(Application).filter_by(application_no="APP-2026-AICTE-1004").first()
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    scheduled_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    scheduled = client.post(
        f"/api/v1/evc/applications/{app.id}",
        json={
            "scheduled_date": scheduled_date,
            "committee_details": {"recommended_mode": "PHYSICAL_VISIT", "venue": "Demo campus"},
        },
        headers=officer_headers,
    )
    assert scheduled.status_code == 200, scheduled.text
    evc_id = scheduled.json()["id"]

    completed = client.post(
        f"/api/v1/evc/{evc_id}/complete",
        json={"findings_summary": "Required facilities were verified.", "outcome": "RECOMMENDED"},
        headers=officer_headers,
    )
    assert completed.status_code == 200, completed.text
    db_session.refresh(app)
    assert app.current_stage_code == "SAC_SHC"
    assert app.workflow_status == "UNDER_REVIEW"
    assert app.assigned_role == "BUREAU_OFFICER"

    bureau = db_session.query(User).filter_by(email="bureau.hq@aicte.gov.in").first()
    bureau_headers = {"Authorization": f"Bearer {_token(bureau)}"}
    recommendation = client.post(
        f"/api/v1/applications/{app.id}/actions",
        json={
            "action": "RECOMMEND_DECISION",
            "decision_status": "RECOMMENDED_APPROVAL",
            "reason": "Inspection report and supporting evidence reviewed.",
        },
        headers=bureau_headers,
    )
    assert recommendation.status_code == 200, recommendation.text
    db_session.refresh(app)
    assert app.current_stage_code == "SAC_SHC"
    assert app.decision_status == "RECOMMENDED_APPROVAL"

    admin = db_session.query(User).filter_by(email="admin@aicte.gov.in").first()
    admin_headers = {"Authorization": f"Bearer {_token(admin)}"}
    final = client.post(
        f"/api/v1/applications/{app.id}/actions",
        json={
            "action": "FINALIZE_DECISION",
            "decision_status": "APPROVED",
            "reason": "Final authority reviewed the bureau recommendation.",
        },
        headers=admin_headers,
    )
    assert final.status_code == 200, final.text
    assert final.json()["current_stage_code"] == "COMPLETED"
    assert final.json()["workflow_status"] == "STAGE_COMPLETED"
    assert final.json()["decision_status"] == "FINAL_APPROVED"


def test_institution_cannot_upload_documents_to_another_institution(
    client, institution_token, db_session
):
    nit = db_session.query(Institution).filter_by(institution_code="NIT-402").first()
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {institution_token}"},
        data={"document_type": "LAND_LEASE_DEED", "institution_id": nit.id},
        files={"file": ("lease.pdf", b"%PDF-1.4 synthetic test", "application/pdf")},
    )
    assert response.status_code == 403


def test_upload_rejects_spoofed_mime_and_disallowed_types(client, institution_token):
    headers = {"Authorization": f"Bearer {institution_token}"}
    spoofed = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"document_type": "LAND_LEASE_DEED"},
        files={"file": ("lease.pdf", b"this is not a pdf", "application/pdf")},
    )
    assert spoofed.status_code == 400

    executable = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"document_type": "LAND_LEASE_DEED"},
        files={"file": ("lease.exe", b"MZ-not-a-document", "application/octet-stream")},
    )
    assert executable.status_code == 400


def test_document_submission_requires_officer_review_and_correction_reason(
    client, institution_token, officer_token, db_session
):
    institution_headers = {"Authorization": f"Bearer {institution_token}"}
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    upload = client.post(
        "/api/v1/documents/upload",
        headers=institution_headers,
        data={"document_type": "LAND_LEASE_DEED"},
        files={"file": ("lease.pdf", b"%PDF-1.4\nSynthetic test document\n%%EOF", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    document_id = upload.json()["id"]
    assert upload.json()["status"] == "SUBMITTED"
    assert "storage_key" not in upload.json()

    institution_review = client.post(
        f"/api/v1/documents/{document_id}/review",
        headers=institution_headers,
        json={"status": "VERIFIED", "remarks": "Looks fine"},
    )
    assert institution_review.status_code == 403

    missing_reason = client.post(
        f"/api/v1/documents/{document_id}/review",
        headers=officer_headers,
        json={"status": "RETURNED_FOR_CORRECTION", "remarks": "x"},
    )
    assert missing_reason.status_code == 422

    returned = client.post(
        f"/api/v1/documents/{document_id}/review",
        headers=officer_headers,
        json={"status": "RETURNED_FOR_CORRECTION", "remarks": "Please provide a signed copy."},
    )
    assert returned.status_code == 200, returned.text
    assert returned.json()["status"] == "RETURNED_FOR_CORRECTION"
    assert returned.json()["verification_remarks"] == "Please provide a signed copy."

    corrected = client.post(
        "/api/v1/documents/upload",
        headers=institution_headers,
        data={"document_type": "LAND_LEASE_DEED", "renewal_of_id": document_id},
        files={"file": ("lease-corrected.pdf", b"%PDF-1.4\nCorrected synthetic document\n%%EOF", "application/pdf")},
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["status"] == "SUBMITTED"
    db_session.expire_all()
    old_document = db_session.query(__import__("app.models.entities", fromlist=["Document"]).Document).filter_by(id=document_id).first()
    assert old_document.status == "SUPERSEDED"


def test_upload_enforces_configured_file_size_limit(client, institution_token, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_BYTES", 40)
    response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {institution_token}"},
        data={"document_type": "LAND_LEASE_DEED"},
        files={"file": ("lease.pdf", b"%PDF-1.4\n" + b"x" * 50 + b"\n%%EOF", "application/pdf")},
    )
    assert response.status_code == 413


def test_regional_officer_without_region_assignment_fails_closed(client, officer_token, db_session):
    officer = db_session.query(User).filter_by(email="officer.north@aicte.gov.in").first()
    officer.region_id = None
    db_session.commit()
    app = db_session.query(Application).first()
    response = client.get(
        f"/api/v1/applications/{app.id}",
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert response.status_code == 403
