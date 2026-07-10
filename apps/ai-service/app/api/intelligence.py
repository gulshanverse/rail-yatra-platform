import logging
from fastapi import APIRouter, HTTPException
from app.engine.core import journey_intelligence_engine
from app.engine.models import TravelRequirement, RankedRecommendation

logger = logging.getLogger("ai-service.api.intelligence")
router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

@router.post("/analyze", response_model=RankedRecommendation)
async def analyze_journey_endpoint(req: TravelRequirement):
    """
    Accepts travel requirements and user preferences, executing the scoring,
    boarding, date, and delay intelligence optimization models.
    """
    logger.info(f"REST API: Journey intelligence analysis requested for {req.source} -> {req.destination}")
    try:
        result = await journey_intelligence_engine.analyze_journey(req)
        return result
    except Exception as e:
        logger.error(f"Error in journey analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Journey intelligence error: {str(e)}")
