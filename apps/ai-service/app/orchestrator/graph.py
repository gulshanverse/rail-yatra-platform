import logging
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END

# Import specialized agents
from app.agents.travel_decision import TravelDecisionAgent
from app.agents.smart_recommendation import SmartRecommendationAgent
from app.agents.prediction import TicketPredictionAgent
from app.agents.pnr import PNRAgent
from app.agents.knowledge import KnowledgeAgent
from app.agents.conversation import ConversationAgent
from app.agents.journey_intelligence import JourneyIntelligenceAgent

# Import intent classifier
from app.orchestrator.classifier import intent_classifier
# Import RAG database
from app.vector.qdrant import qdrant_rag

logger = logging.getLogger("ai-service.orchestrator.graph")

class AgentState(TypedDict):
    user_message: str
    intent: str
    context: Dict[str, Any]
    response: str
    history: List[Dict[str, Any]]

# Initialize agents
travel_agent = TravelDecisionAgent()
rec_agent = SmartRecommendationAgent()
prediction_agent = TicketPredictionAgent()
pnr_agent = PNRAgent()
knowledge_agent = KnowledgeAgent()
conversation_agent = ConversationAgent()
journey_intel_agent = JourneyIntelligenceAgent()

# ----------------- Nodes -----------------

async def classify_input_node(state: AgentState) -> Dict[str, Any]:
    """Classifies the intent of the incoming user request."""
    logger.info("Graph: Executing intent classification node")
    res = await intent_classifier.classify(state["user_message"])
    return {
        "intent": res["intent"],
        "context": {**state.get("context", {}), "classifier_reason": res["reason"]}
    }

async def plan_travel_node(state: AgentState) -> Dict[str, Any]:
    """Handles travel schedule and route searches."""
    logger.info("Graph: Executing plan_travel node")
    # In a real setup, we could call train_search tool first. Let's pass details.
    resp = await travel_agent.run(state["user_message"], state["context"])
    return {"response": resp}

async def recommendation_node(state: AgentState) -> Dict[str, Any]:
    """Handles alternatives scores and fare options comparisons."""
    logger.info("Graph: Executing recommendation node")
    resp = await rec_agent.run(state["user_message"], state["context"])
    return {"response": resp}

async def check_pnr_node(state: AgentState) -> Dict[str, Any]:
    """Handles status checking and verification for tickets."""
    logger.info("Graph: Executing check_pnr node")
    resp = await pnr_agent.run(state["user_message"], state["context"])
    return {"response": resp}

async def knowledge_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves document references from Qdrant and processes knowledge responses."""
    logger.info("Graph: Executing knowledge node")
    # Execute vector search
    docs = qdrant_rag.search_docs(state["user_message"])
    docs_context = "\n".join([f"Source: {d['source']}\nDoc: {d['content']}" for d in docs])
    
    extended_context = {
        **state.get("context", {}),
        "retrieved_vector_knowledge": docs_context
    }
    
    resp = await knowledge_agent.run(state["user_message"], extended_context)
    return {"response": resp}

async def conversation_node(state: AgentState) -> Dict[str, Any]:
    """Handles social chit-chat and greetings."""
    logger.info("Graph: Executing conversation node")
    resp = await conversation_agent.run(state["user_message"], state["context"])
    return {"response": resp}

async def journey_intelligence_node(state: AgentState) -> Dict[str, Any]:
    """Placeholder node for advanced waitlist, delay, fare, and route optimization."""
    logger.info("Graph: Executing journey_intelligence node")
    resp = await journey_intel_agent.run(state["user_message"], state["context"])
    return {"response": resp}

# ----------------- Conditional Edges -----------------

def route_intent(state: AgentState) -> str:
    """Routes execution flow to the appropriate specialized agent node based on intent."""
    intent = state.get("intent", "conversation")
    logger.info(f"Graph Routing: intent is '{intent}'")
    
    mapping = {
        "plan_travel": "plan_travel_node",
        "recommendation": "recommendation_node",
        "check_pnr": "check_pnr_node",
        "knowledge": "knowledge_node",
        "conversation": "conversation_node",
        "journey_intelligence": "journey_intelligence_node"
    }
    
    # Return destination node name
    return mapping.get(intent, "conversation_node")

# ----------------- Graph Construction -----------------

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("classify_node", classify_input_node)
workflow.add_node("plan_travel_node", plan_travel_node)
workflow.add_node("recommendation_node", recommendation_node)
workflow.add_node("check_pnr_node", check_pnr_node)
workflow.add_node("knowledge_node", knowledge_node)
workflow.add_node("conversation_node", conversation_node)
workflow.add_node("journey_intelligence_node", journey_intelligence_node)

# Add Edges
workflow.set_entry_point("classify_node")

# Routing based on intent
workflow.add_conditional_edges(
    "classify_node",
    route_intent,
    {
        "plan_travel_node": "plan_travel_node",
        "recommendation_node": "recommendation_node",
        "check_pnr_node": "check_pnr_node",
        "knowledge_node": "knowledge_node",
        "conversation_node": "conversation_node",
        "journey_intelligence_node": "journey_intelligence_node"
    }
)

# Connect agents to End
workflow.add_edge("plan_travel_node", END)
workflow.add_edge("recommendation_node", END)
workflow.add_edge("check_pnr_node", END)
workflow.add_edge("knowledge_node", END)
workflow.add_edge("conversation_node", END)
workflow.add_edge("journey_intelligence_node", END)

# Compile
compiled_graph = workflow.compile()
