# app/planner/validator.py
from typing import List
from app.planner.models import (
    StructuredTravelPlan,
    ValidationReport,
    Constraint,
    Decision,
)
from app.planner.specifications import (
    AgeEligibleSpecification,
    TimeWindowSpecification,
    DoubleBookingSpecification,
)
from app.planner.policies import (
    LockoutPolicy,
    IdentitySafetyPolicy,
    ConcessionValidationPolicy,
)
from app.planner.errors import PolicyViolationError
from app.planner.interfaces import IPlanValidator


class PlanValidator(IPlanValidator):
    """Domain service to review StructuredTravelPlans against validation rules and policies."""

    def __init__(self):
        self.specifications = [
            AgeEligibleSpecification(),
            TimeWindowSpecification(),
            DoubleBookingSpecification(),
        ]
        self.policies = [
            LockoutPolicy(),
            IdentitySafetyPolicy(),
            ConcessionValidationPolicy(),
        ]

    def validate_plan(self, plan: StructuredTravelPlan) -> ValidationReport:
        is_valid = True
        violated_constraints: List[Constraint] = []
        decisions: List[Decision] = []
        warnings: List[str] = []

        # 1. Evaluate high-level Domain Policies
        for policy in self.policies:
            try:
                policy.evaluate(plan)
                decisions.append(
                    Decision(
                        decision_id=f"DEC-{policy.name.upper()}",
                        reason=f"Policy '{policy.name}' was evaluated and satisfied.",
                        selected_option="PASS",
                    )
                )
            except PolicyViolationError as pve:
                is_valid = False
                violated_constraints.append(
                    Constraint(
                        rule_id=f"POLICY-VIOLATION-{policy.name.upper()}",
                        description=str(pve),
                        category="policy_safety",
                        parameters={"policy_name": policy.name},
                    )
                )
                decisions.append(
                    Decision(
                        decision_id=f"DEC-{policy.name.upper()}",
                        reason=f"Policy '{policy.name}' evaluation failed: {str(pve)}",
                        selected_option="FAIL",
                    )
                )

        # 2. Evaluate Specifications
        for spec in self.specifications:
            spec_name = spec.__class__.__name__
            result = spec.is_satisfied_by(plan)

            if result.is_satisfied:
                decisions.append(
                    Decision(
                        decision_id=f"DEC-{spec_name.upper()}",
                        reason=f"Specification '{spec_name}' checked successfully.",
                        selected_option="PASS",
                    )
                )
            else:
                is_valid = False
                if result.violated_constraint:
                    violated_constraints.append(result.violated_constraint)
                decisions.append(
                    Decision(
                        decision_id=f"DEC-{spec_name.upper()}",
                        reason=f"Specification '{spec_name}' check failed.",
                        selected_option="FAIL",
                    )
                )

        return ValidationReport(
            is_valid=is_valid,
            violated_constraints=violated_constraints,
            decisions=decisions,
            warnings=warnings,
        )
