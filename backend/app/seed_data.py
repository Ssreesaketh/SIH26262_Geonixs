from datetime import datetime, timezone, timedelta, date
from sqlalchemy.orm import Session
from app.models.entities import (
    Region, Institution, User, WorkflowTemplate, Application,
    ApplicationEvent, AuditChainEntry, EVCEvent, Undertaking, Document, Notification
)
from app.core.security import get_password_hash

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def seed_database(db: Session, reset: bool = False):
    """
    Idempotent deterministic seeder for SIH26262 demonstration scenarios.
    """
    if reset:
        # Clear existing data in reverse order of foreign keys
        db.query(Notification).delete()
        # Explicit demo reset also resets the demo audit chain; it is not a production purge mechanism.
        db.query(AuditChainEntry).delete()
        db.query(Document).delete()
        db.query(Undertaking).delete()
        db.query(EVCEvent).delete()
        db.query(ApplicationEvent).delete()
        db.query(Application).delete()
        db.query(User).delete()
        db.query(WorkflowTemplate).delete()
        db.query(Institution).delete()
        db.query(Region).delete()
        db.commit()

    now = utc_now()
    default_pw_hash = get_password_hash("Admin@AICTE2026!")

    # 1. Regions
    regions_data = [
        {"code": "NORTHERN", "name": "Northern Regional Office (Kanpur/Chandigarh)"},
        {"code": "WESTERN", "name": "Western Regional Office (Mumbai)"},
        {"code": "SOUTHERN", "name": "Southern Regional Office (Chennai)"}
    ]
    regions_map = {}
    for r in regions_data:
        existing = db.query(Region).filter(Region.code == r["code"]).first()
        if not existing:
            existing = Region(code=r["code"], name=r["name"])
            db.add(existing)
            db.flush()
        regions_map[r["code"]] = existing

    # 2. Institutions
    institutions_data = [
        {
            "code": "NIT-402",
            "name": "Northern Institute of Technology",
            "region_code": "NORTHERN",
            "email": "contact@nit.edu.in",
            "address": "Sector 14, Institutional Area, Chandigarh"
        },
        {
            "code": "ZEN-801",
            "name": "Zenith Polytechnic & Engineering College",
            "region_code": "NORTHERN",
            "email": "principal@zenith.edu.in",
            "address": "GT Road Industrial Corridor, Kanpur"
        },
        {
            "code": "APX-905",
            "name": "Apex Institute of Technology & Management",
            "region_code": "NORTHERN",
            "email": "admin@apex.edu.in",
            "address": "Bandra-Kurla Complex, Mumbai"
        }
    ]
    institutions_map = {}
    for inst in institutions_data:
        existing = db.query(Institution).filter(Institution.institution_code == inst["code"]).first()
        if not existing:
            existing = Institution(
                institution_code=inst["code"],
                name=inst["name"],
                region_id=regions_map[inst["region_code"]].id,
                contact_email=inst["email"],
                address=inst["address"]
            )
            db.add(existing)
            db.flush()
        institutions_map[inst["code"]] = existing

    # 3. Users
    users_data = [
        {
            "email": "admin@aicte.gov.in",
            "name": "Central System Administrator",
            "role": "SYSTEM_ADMIN",
            "region": None,
            "inst": None
        },
        {
            "email": "officer.north@aicte.gov.in",
            "name": "Dr. Rajesh Sharma (Regional Scrutiny Officer)",
            "role": "REGIONAL_OFFICER",
            "region": "NORTHERN",
            "inst": None
        },
        {
            "email": "bureau.hq@aicte.gov.in",
            "name": "Prof. V. Ramamurthy (Bureau Advisor)",
            "role": "BUREAU_OFFICER",
            "region": None,
            "inst": None
        },
        {
            "email": "principal@zenith.edu.in",
            "name": "Dr. Sunita Verma (Principal, Zenith)",
            "role": "INSTITUTION_USER",
            "region": "NORTHERN",
            "inst": "ZEN-801"
        },
        {
            "email": "principal@nit.edu.in",
            "name": "Dr. H.S. Gill (Principal, NIT)",
            "role": "INSTITUTION_USER",
            "region": "NORTHERN",
            "inst": "NIT-402"
        },
        {
            "email": "admin@apex.edu.in",
            "name": "Ms. Ananya Rao (Institution Administrator, Apex)",
            "role": "INSTITUTION_USER",
            "region": "NORTHERN",
            "inst": "APX-905"
        }
    ]
    users_map = {}
    for u in users_data:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            reg_id = regions_map[u["region"]].id if u["region"] else None
            inst_id = institutions_map[u["inst"]].id if u["inst"] else None
            existing = User(
                email=u["email"],
                password_hash=default_pw_hash,
                display_name=u["name"],
                role=u["role"],
                region_id=reg_id,
                institution_id=inst_id,
                is_active=True
            )
            db.add(existing)
            db.flush()
        users_map[u["email"]] = existing

    # 4. Workflow Templates
    wf_templates = [
        {
            "code": "SCRUTINY_EVC",
            "name": "Comprehensive Scrutiny + EVC + Committee Route",
            "version": 1,
            "configuration": {
                "ordered_stages": ["SCRUTINY", "EVC", "SAC_SHC", "COMPLETED"],
                "stage_roles": {"DRAFT": "INSTITUTION_USER", "SCRUTINY": "REGIONAL_OFFICER", "EVC": "REGIONAL_OFFICER", "SAC_SHC": "BUREAU_OFFICER", "COMPLETED": "SYSTEM_ADMIN"},
                "final_decision_role": "SYSTEM_ADMIN",
                "stage_slas": {"SCRUTINY": 7, "EVC": 14, "SAC_SHC": 10, "COMPLETED": 0},
                "rectification_sla_days": 10,
                "warning_threshold_percent": 80,
                "reminder_windows_hours": [48, 24],
                "escalation_ladder": [{"after_days": 0, "recipient_role": "REGIONAL_OFFICER"}, {"after_days": 3, "recipient_role": "BUREAU_OFFICER"}, {"after_days": 7, "recipient_role": "SYSTEM_ADMIN"}]
            }
        },
        {
            "code": "ONLY_SCRUTINY",
            "name": "Fast-Track Only Scrutiny (Routine EoA)",
            "version": 1,
            "configuration": {
                "ordered_stages": ["SCRUTINY", "COMPLETED"],
                "stage_roles": {"DRAFT": "INSTITUTION_USER", "SCRUTINY": "REGIONAL_OFFICER", "COMPLETED": "SYSTEM_ADMIN"},
                "final_decision_role": "SYSTEM_ADMIN",
                "stage_slas": {"SCRUTINY": 7, "COMPLETED": 0},
                "rectification_sla_days": 7,
                "warning_threshold_percent": 80,
                "reminder_windows_hours": [48, 24],
                "escalation_ladder": [{"after_days": 0, "recipient_role": "REGIONAL_OFFICER"}, {"after_days": 3, "recipient_role": "BUREAU_OFFICER"}, {"after_days": 7, "recipient_role": "SYSTEM_ADMIN"}]
            }
        },
        {
            "code": "EVC_SAC_SHC",
            "name": "Special Inspection & Hearing Route",
            "version": 1,
            "configuration": {
                "ordered_stages": ["EVC", "SAC_SHC", "COMPLETED"],
                "stage_roles": {"DRAFT": "INSTITUTION_USER", "EVC": "REGIONAL_OFFICER", "SAC_SHC": "BUREAU_OFFICER", "COMPLETED": "SYSTEM_ADMIN"},
                "final_decision_role": "SYSTEM_ADMIN",
                "stage_slas": {"EVC": 14, "SAC_SHC": 10, "COMPLETED": 0},
                "rectification_sla_days": 10,
                "warning_threshold_percent": 80,
                "reminder_windows_hours": [48, 24],
                "escalation_ladder": [{"after_days": 0, "recipient_role": "REGIONAL_OFFICER"}, {"after_days": 3, "recipient_role": "BUREAU_OFFICER"}, {"after_days": 7, "recipient_role": "SYSTEM_ADMIN"}]
            }
        }
    ]
    wf_map = {}
    for wt in wf_templates:
        existing = db.query(WorkflowTemplate).filter(
            WorkflowTemplate.code == wt["code"],
            WorkflowTemplate.version == wt["version"]
        ).first()
        if not existing:
            existing = WorkflowTemplate(
                code=wt["code"],
                name=wt["name"],
                version=wt["version"],
                configuration=wt["configuration"]
            )
            db.add(existing)
            db.flush()
        wf_map[wt["code"]] = existing

    # 5. Seed Demonstration Applications (Section 15)
    default_wf = wf_map["SCRUTINY_EVC"]

    # Scenario 1: Fresh submission in Scrutiny
    app1_no = "APP-2026-AICTE-1001"
    app1 = db.query(Application).filter(Application.application_no == app1_no).first()
    if not app1:
        app1 = Application(
            application_no=app1_no,
            institution_id=institutions_map["NIT-402"].id,
            application_type="EXTENSION_OF_APPROVAL",
            workflow_template_id=default_wf.id,
            workflow_version=1,
            current_stage_code="SCRUTINY",
            workflow_status="UNDER_REVIEW",
            decision_status="NOT_RECORDED",
            assigned_role="REGIONAL_OFFICER",
            submitted_at=now - timedelta(days=1),
            stage_entered_at=now - timedelta(days=1),
            stage_due_at=now + timedelta(days=6)
        )
        db.add(app1)
        db.flush()

        # Audit Event
        ev = ApplicationEvent(
            application_id=app1.id,
            actor_user_id=users_map["principal@nit.edu.in"].id,
            actor_role="INSTITUTION_USER",
            action="SUBMIT",
            from_stage="DRAFT",
            to_stage="SCRUTINY",
            reason="Application submitted for annual Extension of Approval."
        )
        db.add(ev)

    # Scenario 2: Application with Deficiency Return
    app2_no = "APP-2026-AICTE-1002"
    app2 = db.query(Application).filter(Application.application_no == app2_no).first()
    if not app2:
        app2 = Application(
            application_no=app2_no,
            institution_id=institutions_map["ZEN-801"].id,
            application_type="INTAKE_VARIATION",
            workflow_template_id=default_wf.id,
            workflow_version=1,
            current_stage_code="SCRUTINY",
            workflow_status="DEFICIENCY_RETURNED",
            decision_status="NOT_RECORDED",
            assigned_role="INSTITUTION_USER",
            submitted_at=now - timedelta(days=5),
            stage_entered_at=now - timedelta(days=2),
            stage_due_at=now + timedelta(days=8)
        )
        db.add(app2)
        db.flush()

        ev2 = ApplicationEvent(
            application_id=app2.id,
            actor_user_id=users_map["officer.north@aicte.gov.in"].id,
            actor_role="REGIONAL_OFFICER",
            action="RETURN_DEFICIENCY",
            from_stage="SCRUTINY",
            to_stage="SCRUTINY",
            reason="Municipal Water Connection NOC missing from Annexure IV; building plan lacks fire egress clearance.",
            metadata_json={"deficiency_remarks": "Municipal Water Connection NOC missing from Annexure IV."}
        )
        db.add(ev2)

    # Scenario 3: Application Awaiting EVC Scheduling
    app4_no = "APP-2026-AICTE-1004"
    app4 = db.query(Application).filter(Application.application_no == app4_no).first()
    if not app4:
        app4 = Application(
            application_no=app4_no,
            institution_id=institutions_map["APX-905"].id,
            application_type="NEW_INSTITUTION",
            workflow_template_id=default_wf.id,
            workflow_version=1,
            current_stage_code="EVC",
            workflow_status="UNDER_REVIEW",
            decision_status="NOT_RECORDED",
            assigned_role="REGIONAL_OFFICER",
            submitted_at=now - timedelta(days=12),
            stage_entered_at=now - timedelta(days=3),
            stage_due_at=now + timedelta(days=11)
        )
        db.add(app4)
        db.flush()

        evc4 = EVCEvent(
            application_id=app4.id,
            status="PENDING_SCHEDULE",
            scheduling_deadline=now + timedelta(days=4),
            committee_details={"recommended_mode": "PHYSICAL_VISIT"}
        )
        db.add(evc4)

    # Scenario 4: EVC visit already scheduled; demonstrates upcoming inspection.
    app3_no = "APP-2026-AICTE-1003"
    app3 = db.query(Application).filter(Application.application_no == app3_no).first()
    if not app3:
        app3 = Application(
            application_no=app3_no,
            institution_id=institutions_map["ZEN-801"].id,
            application_type="EXTENSION_OF_APPROVAL",
            workflow_template_id=default_wf.id,
            workflow_version=1,
            current_stage_code="EVC",
            workflow_status="SCHEDULED",
            decision_status="NOT_RECORDED",
            assigned_role="REGIONAL_OFFICER",
            submitted_at=now - timedelta(days=10),
            stage_entered_at=now - timedelta(days=2),
            stage_due_at=now + timedelta(days=12)
        )
        db.add(app3)
        db.flush()
        db.add(EVCEvent(
            application_id=app3.id,
            status="SCHEDULED",
            scheduled_date=now + timedelta(days=5),
            scheduling_deadline=now + timedelta(days=3),
            committee_details={"recommended_mode": "PHYSICAL_VISIT", "venue": "Institution campus"}
        ))

    # Scenario 5: EVC completed and awaiting bureau review.
    app5_no = "APP-2026-AICTE-1005"
    app5 = db.query(Application).filter(Application.application_no == app5_no).first()
    if not app5:
        app5 = Application(
            application_no=app5_no,
            institution_id=institutions_map["NIT-402"].id,
            application_type="NEW_INSTITUTION",
            workflow_template_id=default_wf.id,
            workflow_version=1,
            current_stage_code="SAC_SHC",
            workflow_status="UNDER_REVIEW",
            decision_status="NOT_RECORDED",
            assigned_role="BUREAU_OFFICER",
            submitted_at=now - timedelta(days=20),
            stage_entered_at=now - timedelta(days=2),
            stage_due_at=now + timedelta(days=8)
        )
        db.add(app5)
        db.flush()
        db.add(EVCEvent(
            application_id=app5.id,
            status="FINDINGS_SUBMITTED",
            scheduled_date=now - timedelta(days=4),
            scheduling_deadline=now - timedelta(days=6),
            committee_details={"recommended_mode": "PHYSICAL_VISIT", "venue": "Institution campus"},
            findings_summary="Infrastructure and laboratory verification completed; supporting evidence recorded.",
            created_at=now - timedelta(days=4),
            completed_at=now - timedelta(days=4)
        ))
        db.add(ApplicationEvent(
            application_id=app5.id,
            actor_user_id=users_map["officer.north@aicte.gov.in"].id,
            actor_role="REGIONAL_OFFICER",
            action="EVC_FINDINGS_SUBMITTED",
            from_stage="EVC",
            to_stage="SAC_SHC",
            reason="Inspection report submitted for bureau review."
        ))

    # 6. Seed Undertakings (Section 15)
    # Scenario 4: Undertaking due soon (48h)
    und1 = db.query(Undertaking).filter(Undertaking.title == "AI & Robotics Laboratory Setup").first()
    if not und1 and app1:
        und1 = Undertaking(
            application_id=app1.id,
            institution_id=institutions_map["NIT-402"].id,
            title="AI & Robotics Laboratory Setup",
            description="Procure and commission 30 GPUs and robotic arms as committed under curriculum upgrade.",
            due_at=now + timedelta(hours=48),
            status="PENDING"
        )
        db.add(und1)

    # Scenario 5: Overdue compliance obligation (5 days overdue)
    und2 = db.query(Undertaking).filter(Undertaking.title == "Fire Extinguisher & Safety Valve Replacement").first()
    if not und2 and app2:
        und2 = Undertaking(
            application_id=app2.id,
            institution_id=institutions_map["ZEN-801"].id,
            title="Fire Extinguisher & Safety Valve Replacement",
            description="Replace expired carbon dioxide fire extinguishing cylinders across Workshop blocks A & B.",
            due_at=now - timedelta(days=5),
            status="PENDING"
        )
        db.add(und2)

    # Scenario 8: Submitted evidence awaiting verification
    und3 = db.query(Undertaking).filter(Undertaking.title == "Faculty Cadre Ratio Recruitment (5 Ph.D. Professors)").first()
    if not und3 and app4:
        und3 = Undertaking(
            application_id=app4.id,
            institution_id=institutions_map["APX-905"].id,
            title="Faculty Cadre Ratio Recruitment (5 Ph.D. Professors)",
            description="Recruit 5 full-time Ph.D. Computer Science professors in compliance with AICTE norms.",
            due_at=now + timedelta(days=15),
            status="SUBMITTED",
            submitted_at=now - timedelta(hours=12),
            evidence_summary="Appointment letters and joining reports for 5 Ph.D. faculty attached for verification."
        )
        db.add(und3)

    # 7. Seed Documents & Expiry Scenarios (Section 15)
    today = now.date()
    # Scenario 6: Lease document expiring soon (15 days)
    doc1 = db.query(Document).filter(Document.display_name == "Registered Land Lease Deed - 30 Years").first()
    if not doc1:
        doc1 = Document(
            application_id=app1.id if app1 else None,
            institution_id=institutions_map["NIT-402"].id,
            document_type="LAND_LEASE_DEED",
            display_name="Registered Land Lease Deed - 30 Years",
            storage_key="sample_lease_deed_nit402.pdf",
            mime_type="application/pdf",
            file_size=248000,
            expiry_date=today + timedelta(days=15),
            status="EXPIRING_SOON",
            submitted_at=now - timedelta(days=100)
        )
        db.add(doc1)

    # Scenario 7: Expired document awaiting renewal (10 days ago)
    doc2 = db.query(Document).filter(Document.display_name == "State Fire & Rescue Services NOC").first()
    if not doc2:
        doc2 = Document(
            application_id=app2.id if app2 else None,
            institution_id=institutions_map["ZEN-801"].id,
            document_type="FIRE_NOC",
            display_name="State Fire & Rescue Services NOC",
            storage_key="sample_fire_noc_zen801.pdf",
            mime_type="application/pdf",
            file_size=184000,
            expiry_date=today - timedelta(days=10),
            status="EXPIRED",
            submitted_at=now - timedelta(days=375)
        )
        db.add(doc2)

    db.commit()
    print("Database seeding completed successfully.")
