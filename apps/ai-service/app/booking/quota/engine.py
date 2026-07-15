# app/booking/quota/engine.py
from typing import Dict, Any
from app.booking.interfaces.contracts import IQuotaEngine
from app.booking.dto.models import QuotaDTO


class QuotaEngine(IQuotaEngine):
    def resolve_quotas(
        self, profile: Dict[str, Any], seat_pools: Any
    ) -> QuotaDTO:
        # Resolves dynamic passenger criteria eligibility
        eligible = ["GN"]
        
        is_female = profile.get("is_female", False)
        is_senior = profile.get("is_senior", False)
        is_disabled = profile.get("is_disabled", False)
        
        if is_female:
            eligible.append("LD")
        if is_senior:
            eligible.append("SS")
        if is_disabled:
            eligible.append("HP")
            
        target = "GN"
        # Prioritize quotas
        if "HP" in eligible:
            target = "HP"
        elif "SS" in eligible:
            target = "SS"
        elif "LD" in eligible:
            target = "LD"
            
        return QuotaDTO(
            quota_code=target,
            eligible_quotas=eligible,
            is_eligible=True
        )
