
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.entities import (
    Application,
    WorkflowTemplate,
    User,
)
from app.services.audit_service import AuditService


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


DEFAULT_STAGE_SLAS = {
    "DRAFT": 30,
    "SCRUTINY": 7,
    "EVC": 14,
    "SAC_SHC": 10,
    "COMPLETED": 0,
}

# Default ownership of each stage.
# Workflow templates can override this with a "stage_roles" mapping.
DEFAULT_STAGE_ROLES = {
    "DRAFT": "INSTITUTION_USER",
    "SCRUTINY": "REGIONAL_OFFICER",
    "EVC": "REGIONAL_OFFICER",
    "SAC_SHC": "BUREAU_OFFICER",
    "COMPLETED": "SYSTEM_ADMIN",
}

DEFAULT_ORDERED_STAGES = [
    "SCRUTINY",
    "EVC",
    "SAC_SHC",
    "COMPLETED",
]

VALID_RECOMMENDATIONS = {
    "RECOMMENDED_APPROVAL",
    "RECOMMENDED_REJECTION",
}


def normalize_code(value: Any) -> str:
    """Normalize strings and enum values into comparable workflow codes."""
    if value is None:
        return ""

    value = getattr(value, "value", value)
    return str(value).strip().upper().replace("-", "_").replace(" ", "_")


def normalize_role(value: Any) -> str:
    """Normalize a role name."""
    return normalize_code(value)


def normalize_stage(value: Any) -> str:
    """Normalize known stage aliases."""
    stage = normalize_code(value)

    aliases = {
        "DRAFT_SUBMISSION": "DRAFT",
        "SCRUTINY_REVIEW": "SCRUTINY",
        "EVC_INSPECTION": "EVC",
        "SAC_SHC_COMMITTEE": "SAC_SHC",
        "STATUTORY_COMPLETION": "COMPLETED",
        "COMPLETION": "COMPLETED",
    }

    return aliases.get(stage, stage)


def normalize_status(value: Any) -> str:
    """Normalize workflow status."""
    return normalize_code(value)


class WorkflowEngine:
    @staticmethod
    def _configuration(application: Application) -> Dict[str, Any]:
        template: Optional[WorkflowTemplate] = application.workflow_template
        if template is None or not template.configuration:
            return {}
        return dict(template.configuration)

    @staticmethod
    def _ordered_stages(config: Dict[str, Any]) -> List[str]:
        configured = config.get("ordered_stages", DEFAULT_ORDERED_STAGES)

        if not isinstance(configured, list) or not configured:
            configured = DEFAULT_ORDERED_STAGES

        stages = [normalize_stage(stage) for stage in configured]
        return stages or list(DEFAULT_ORDERED_STAGES)

    @staticmethod
    def _stage_role(stage: str, config: Dict[str, Any]) -> str:
        stage_roles = dict(DEFAULT_STAGE_ROLES)
        custom_roles = config.get("stage_roles", {})

        if isinstance(custom_roles, dict):
            for key, value in custom_roles.items():
                stage_roles[normalize_stage(key)] = normalize_role(value)

        return stage_roles.get(stage, "SYSTEM_ADMIN")

    @staticmethod
    def _route_to_stage(application: Application, stage: str, config: Dict[str, Any]) -> None:
        """Update stage ownership when the workflow moves."""
        application.current_stage_code = stage
        application.assigned_role = WorkflowEngine._stage_role(stage, config)

    @staticmethod
    def get_permitted_actions(
        application: Application,
        current_user: User,
    ) -> List[str]:
        """
        Return the actions authorized for the current role and workflow state.

        Role responsibilities:
        - Institution user: submit or resubmit.
        - Regional officer: scrutiny review.
        - EVC member: record inspection observations.
        - Bureau officer: committee-stage recommendation.
        - System admin: operational override using the same stage-specific rules.
        """
        role = normalize_role(current_user.role)
        stage = normalize_stage(application.current_stage_code)
        wf_status = normalize_status(application.workflow_status)

        if stage == "COMPLETED" or wf_status == "STAGE_COMPLETED":
            return []

        config = WorkflowEngine._configuration(application)
        permitted: List[str] = []

        if role == "INSTITUTION_USER":
            if stage == "DRAFT" and wf_status == "DRAFT":
                permitted.append("SUBMIT")
            elif wf_status == "DEFICIENCY_RETURNED":
                permitted.append("RESUBMIT")

        if role == "REGIONAL_OFFICER":
            if stage == "SCRUTINY" and wf_status in {
                "SUBMITTED",
                "UNDER_REVIEW",
            }:
                permitted.extend(["ADVANCE", "RETURN_DEFICIENCY"])

        if role == "BUREAU_OFFICER":
            if stage == "SAC_SHC" and wf_status == "UNDER_REVIEW":
                permitted.extend(["RECOMMEND_DECISION", "RETURN_DEFICIENCY"])

        if role == "SYSTEM_ADMIN":
            if (
                stage == "SAC_SHC"
                and wf_status == "UNDER_REVIEW"
                and application.decision_status in VALID_RECOMMENDATIONS
            ):
                permitted.append("FINALIZE_DECISION")

        # Bureau officers may return an EVC case for deficiencies, but do not
        # advance the case through the EVC inspection on behalf of the EVC team.
        if role == "BUREAU_OFFICER":
            if stage == "EVC" and wf_status in {"UNDER_REVIEW", "SCHEDULED"}:
                permitted.append("RETURN_DEFICIENCY")

        return permitted

    @staticmethod
    def execute_transition(
        db: Session,
        application: Application,
        actor: User,
        action: str,
        reason: Optional[str] = None,
        target_stage: Optional[str] = None,
        decision_status: Optional[str] = None,
    ) -> Application:
        """Validate, execute, and audit a workflow action."""
        action = normalize_code(action)
        role = normalize_role(actor.role)
        from_stage = normalize_stage(application.current_stage_code)
        wf_status = normalize_status(application.workflow_status)

        permitted = WorkflowEngine.get_permitted_actions(application, actor)

        if action not in permitted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Action '{action}' is not permitted in stage "
                    f"'{from_stage}' with status '{wf_status}' "
                    f"for role '{role}'."
                ),
            )

        config = WorkflowEngine._configuration(application)
        stage_slas = config.get("stage_slas", DEFAULT_STAGE_SLAS)

        if not isinstance(stage_slas, dict):
            stage_slas = DEFAULT_STAGE_SLAS

        ordered_stages = WorkflowEngine._ordered_stages(config)
        now = utc_now()
        to_stage = from_stage
        metadata: Dict[str, Any] = {}

        if action == "SUBMIT":
            next_stage = ordered_stages[0]

            WorkflowEngine._route_to_stage(application, next_stage, config)
            application.workflow_status = "UNDER_REVIEW"
            application.submitted_at = now
            application.stage_entered_at = now
            application.stage_due_at = now + timedelta(
                days=int(stage_slas.get(next_stage, 7))
            )
            to_stage = next_stage

        elif action == "ADVANCE":
            requested_stage = normalize_stage(target_stage) if target_stage else ""

            if requested_stage:
                if requested_stage not in ordered_stages:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="The requested target stage is not configured.",
                    )

                current_index = (
                    ordered_stages.index(from_stage)
                    if from_stage in ordered_stages
                    else -1
                )
                target_index = ordered_stages.index(requested_stage)

                if target_index != current_index + 1:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Applications can only advance to the next configured stage.",
                    )

                next_stage = requested_stage
            else:
                try:
                    current_index = ordered_stages.index(from_stage)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Current stage '{from_stage}' is not in the configured workflow.",
                    )

                if current_index + 1 >= len(ordered_stages):
                    next_stage = "COMPLETED"
                else:
                    next_stage = ordered_stages[current_index + 1]

            WorkflowEngine._route_to_stage(application, next_stage, config)
            application.workflow_status = (
                "STAGE_COMPLETED"
                if next_stage == "COMPLETED"
                else "UNDER_REVIEW"
            )
            application.stage_entered_at = now
            application.stage_due_at = now + timedelta(
                days=int(stage_slas.get(next_stage, 7))
            )
            to_stage = next_stage

        elif action == "RETURN_DEFICIENCY":
            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "A detailed reason is mandatory when returning "
                        "an application for deficiencies."
                    ),
                )

            application.workflow_status = "DEFICIENCY_RETURNED"
            application.assigned_role = "INSTITUTION_USER"
            application.stage_entered_at = now

            rectification_days = int(
                config.get("rectification_sla_days", 10)
            )
            application.stage_due_at = now + timedelta(
                days=rectification_days
            )
            metadata["deficiency_remarks"] = reason.strip()

        elif action == "RESUBMIT":
            application.workflow_status = "UNDER_REVIEW"
            application.assigned_role = WorkflowEngine._stage_role(
                from_stage, config
            )
            application.stage_entered_at = now
            application.stage_due_at = now + timedelta(
                days=int(stage_slas.get(from_stage, 7))
            )
            metadata["resubmission_notes"] = (
                reason.strip()
                if reason and reason.strip()
                else "Applicant resubmitted response to deficiency notice."
            )

        elif action == "RECORD_OBSERVATIONS":
            if role != "REGIONAL_OFFICER" or from_stage != "EVC":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the Regional Officer can record EVC observations.",
                )

            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Inspection observations are required.",
                )

            # Recording observations does not itself advance the workflow.
            metadata["evc_observations"] = reason.strip()
            application.workflow_status = "UNDER_REVIEW"

        elif action == "RECOMMEND_DECISION":
            if role not in {"BUREAU_OFFICER", "SYSTEM_ADMIN"} or from_stage != "SAC_SHC":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only an authorized Bureau Officer can record a committee recommendation.",
                )

            recommendation = normalize_code(decision_status)

            if recommendation not in VALID_RECOMMENDATIONS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Decision recommendation must be "
                        "RECOMMENDED_APPROVAL or RECOMMENDED_REJECTION."
                    ),
                )

            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="A committee rationale is required.",
                )

            # Preserve the distinction between a committee recommendation
            # and final statutory completion. The application remains at
            # SAC_SHC for a designated final authority to process.
            application.decision_status = recommendation
            application.workflow_status = "UNDER_REVIEW"
            application.assigned_role = normalize_role(
                config.get("final_decision_role", "SYSTEM_ADMIN")
            )
            metadata["decision_recorded"] = recommendation
            metadata["committee_rationale"] = reason.strip()
            metadata["recommendation_recorded"] = True

        elif action == "FINALIZE_DECISION":
            if role != "SYSTEM_ADMIN" or from_stage != "SAC_SHC":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the designated final authority can record the final decision.",
                )
            if application.decision_status not in VALID_RECOMMENDATIONS:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A bureau recommendation must be recorded before the final decision.",
                )
            if not reason or not reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="A reason is required for the final authority decision.",
                )
            final_decision = normalize_code(decision_status)
            if final_decision not in {"APPROVED", "REJECTED"}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Final decision must be APPROVED or REJECTED.",
                )
            prior_recommendation = application.decision_status
            application.current_stage_code = "COMPLETED"
            application.workflow_status = "STAGE_COMPLETED"
            application.decision_status = f"FINAL_{final_decision}"
            application.assigned_role = "SYSTEM_ADMIN"
            application.stage_entered_at = now
            application.stage_due_at = now
            to_stage = "COMPLETED"
            metadata["final_decision"] = final_decision
            metadata["bureau_recommendation"] = prior_recommendation

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported workflow action '{action}'.",
            )

        application.updated_at = now

        audit_action = "FINAL_DECISION" if action == "FINALIZE_DECISION" else action
        AuditService.record_event(
            db=db,
            application_id=application.id,
            actor=actor,
            action=audit_action,
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason,
            metadata_json=metadata,
        )

        db.flush()
        return application
