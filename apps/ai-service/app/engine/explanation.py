import logging
from typing import List, Dict, Any

logger = logging.getLogger("ai-service.engine.explanation")

def generate_option_explanations(option: Dict[str, Any], sub_scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Analyzes scores and stats of a travel option to deterministically compile
    its list of advantages, disadvantages, and reasoning summary.
    """
    advantages = []
    disadvantages = []
    
    # 1. Cost analysis
    if sub_scores["cost"] >= 80:
        advantages.append(f"Budget-friendly fare: Rs. {option['fare']}")
    elif sub_scores["cost"] <= 45:
        disadvantages.append(f"Premium fare pricing: Rs. {option['fare']}")

    # 2. Comfort analysis
    if sub_scores["comfort"] >= 85:
        advantages.append(f"High comfort tier ({option['booking_class']} class)")
    elif sub_scores["comfort"] <= 40:
        disadvantages.append(f"Basic sleeper class (low comfort on long transits)")

    # 3. Speed/Duration analysis
    advantages.append(f"Duration: {option['duration']}")
    if sub_scores["speed"] >= 85:
        advantages.append("Superfast express speed (saves travel hours)")

    # 4. Reliability/Delay analysis
    if option["predicted_delay_mins"] <= 15:
        advantages.append(f"Highly punctual (Avg. Delay: {option['predicted_delay_mins']} mins)")
    else:
        disadvantages.append(f"Risk of delay: ~{option['predicted_delay_mins']} minutes late average")

    # 5. Waitlist clearing analysis
    if option["confirmation_probability"] >= 90:
        advantages.append(f"High confirmation probability ({option['confirmation_probability']}% clearance)")
    elif option["confirmation_probability"] <= 50:
        disadvantages.append(f"Low waitlist clearance chance ({option['confirmation_probability']}% clearing probability)")

    # Format tags for display
    if option.get("is_alternative_station"):
        advantages.append(f"Alternative boarding point: {option['source']} (original: {option['original_boarding_station']})")
    if option.get("is_alternative_date"):
        advantages.append(f"Alternative date: {option['journey_date']} (original: {option['original_journey_date']})")

    # Construct reasoning snippet
    reasoning = (
        f"This option is rated at {option['overall_score']}/100. "
        f"It offers a {option['booking_class']} ticket at Rs. {option['fare']} with a predicted delay of {option['predicted_delay_mins']} mins. "
        f"Waitlist/Booking status is currently {option['waitlist_status']}, resulting in a clearing confidence of {option['confirmation_probability']}%."
    )

    return {
        "advantages": advantages,
        "disadvantages": disadvantages,
        "reasoning": reasoning
    }

def compile_tradeoffs_report(options: List[Any]) -> str:
    """
    Compiles a structured markdown summary comparing all options.
    """
    if not options:
        return "No options available for evaluation."

    # Sort options by overall_score descending
    sorted_options = sorted(options, key=lambda x: x.overall_score, reverse=True)
    best = sorted_options[0]

    report = (
        f"## Journey Intelligence Trade-Off Matrix\n\n"
        f"Based on your requirements, the best choice is **{best.train_name} ({best.train_number})** "
        f"scoring **{best.overall_score}/100** (Confidence Score: **{int(best.confidence_score * 100)}%**).\n\n"
        f"### Summary of Alternatives:\n\n"
    )

    for i, opt in enumerate(sorted_options):
        alt_label = ""
        if opt.is_alternative_station:
            alt_label = " *(Alternate Station)*"
        elif opt.is_alternative_date:
            alt_label = " *(Alternate Date)*"

        report += (
            f"{i+1}. **{opt.train_name}** | Class: **{opt.booking_class}** | Score: **{opt.overall_score}**{alt_label}\n"
            f"   - **Reason Codes**: `{', '.join(opt.reason_codes)}` | Fare: Rs. {opt.fare} | Predicted Delay: {opt.predicted_delay_mins} mins\n"
            f"   - **Pros**: {', '.join(opt.advantages[:3])}\n"
        )
        if opt.disadvantages:
            report += f"   - **Cons**: {', '.join(opt.disadvantages[:2])}\n"
        report += "\n"

    report += (
        f"### Decisive Trade-Off Analysis:\n"
        f"- **Comfort vs. Cost**: Shifting to premium AC classes (1A/2A) offers a significant comfort index (+40 points) but increases dynamic pricing by ~Rs. 1,200.\n"
        f"- **Junction Routing**: Boarding from adjacent junctions may improve confirmation probability by up to 25% due to station quotas."
    )

    return report
