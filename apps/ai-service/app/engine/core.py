import logging
from typing import List, Dict, Any
from app.engine.models import TravelRequirement, TravelOption, RankedRecommendation
from app.tools.train_search import search_trains
from app.engine.prediction import predict_journey_metrics
from app.engine.scoring import scoring_engine
from app.engine.boarding import optimize_boarding_stations
from app.engine.date_optimizer import optimize_travel_dates
from app.engine.explanation import generate_option_explanations, compile_tradeoffs_report

logger = logging.getLogger("ai-service.engine.core")

class JourneyIntelligenceEngine:
    """
    Core orchestrating engine for travel decision optimizations.
    Merges deterministic search results, alternative routes, boarding junctions,
    delay forecasts, and personalized weighting matrices.
    """
    def __init__(self):
        pass

    async def analyze_journey(self, req: TravelRequirement) -> RankedRecommendation:
        logger.info(f"Analyzing travel request: {req.source} -> {req.destination} (date: {req.journey_date})")

        # 1. Gather raw travel choices
        raw_options: List[Dict[str, Any]] = []

        # Standard direct routes
        direct_trains = search_trains(req.source, req.destination)
        for train in direct_trains:
            # Determine initial waitlist status
            wl_status = "Available 18"
            if req.current_wl_position:
                wl_status = f"WL {req.current_wl_position}"
            elif "Rajdhani" in train["name"]:
                wl_status = "WL 14"
            elif "Kerala" in train["name"]:
                wl_status = "WL 25"
                
            raw_options.append({
                "train_number": train["train_number"],
                "train_name": train["name"],
                "source": req.source,
                "destination": req.destination,
                "departure": train["departure"],
                "arrival": train["arrival"],
                "duration": train["duration"],
                "booking_class": req.preferred_class,
                "fare": train["base_fare"].get(req.preferred_class, 1200),
                "waitlist_status": wl_status,
                "journey_date": req.journey_date
            })

        # Alternative station junctions
        alt_boarding = optimize_boarding_stations(req.source, req.destination, req.preferred_class, req.journey_date)
        raw_options.extend(alt_boarding)

        # Alternative travel dates (±2 days)
        alt_dates = optimize_travel_dates(req.source, req.destination, req.journey_date, req.preferred_class)
        raw_options.extend(alt_dates)

        # 2. Enrich, Score, and Compile details for each option
        enriched_options: List[TravelOption] = []
        
        # We assume 500km as average distance if station details are not fully resolved
        distance = 500
        if req.source == "NDLS" and req.destination == "MAS":
            distance = 2100
        elif req.source == "NDLS" and req.destination == "SBC":
            distance = 2400
        elif req.source == "HWH" and req.destination == "CSMT":
            distance = 1960

        for opt in raw_options:
            # Run prediction sub-module
            wl_pos = 0
            if "WL" in opt["waitlist_status"]:
                try:
                    wl_pos = int(opt["waitlist_status"].split(" ")[1])
                except Exception:
                    wl_pos = 15
            
            # Predict delay & confirmation clearance
            pred = predict_journey_metrics(
                opt["train_number"],
                opt["booking_class"],
                wl_pos
            )
            
            # Merge predicted values
            opt["predicted_delay_mins"] = pred["predicted_delay_mins"]
            opt["confirmation_probability"] = pred["confirmation_probability"]
            opt["confidence_score"] = pred["confidence_score"]

            # Run scoring sub-scores calculations
            sub_scores = scoring_engine.compute_sub_scores(opt, distance)
            
            # Run overall score mapping using weights
            opt["overall_score"] = scoring_engine.calculate_overall_score(sub_scores, req.preferences)

            # Map reason codes
            opt["reason_codes"] = scoring_engine.determine_reason_codes(sub_scores, opt)

            # Generate advantages/disadvantages list
            expl = generate_option_explanations(opt, sub_scores)
            opt["advantages"] = expl["advantages"]
            opt["disadvantages"] = expl["disadvantages"]
            opt["reasoning"] = expl["reasoning"]

            # Convert to Pydantic object
            enriched_options.append(TravelOption(**opt))

        # 3. Sort options by overall score descending
        enriched_options.sort(key=lambda x: x.overall_score, reverse=True)

        # 4. Compile human-readable tradeoffs explanation matrix
        tradeoffs = compile_tradeoffs_report(enriched_options)

        return RankedRecommendation(
            requirement=req,
            options=enriched_options,
            best_option_index=0,
            tradeoffs_summary=tradeoffs
        )

journey_intelligence_engine = JourneyIntelligenceEngine()
