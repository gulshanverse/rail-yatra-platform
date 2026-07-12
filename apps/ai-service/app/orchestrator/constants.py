# Domain constants for RailYatra AI Orchestration layer

# Intent Names
INTENT_TRAVEL_PLANNING = "plan_travel"
INTENT_PREDICTION = "journey_intelligence"  # Maps classifier output
INTENT_PNR = "check_pnr"                    # Maps classifier output
INTENT_KNOWLEDGE = "knowledge"
INTENT_CONVERSATION = "conversation"
INTENT_RECOMMENDATION = "recommendation"

# Agent Names/Keys
AGENT_TRAVEL_PLANNING = "travel_decision"
AGENT_PREDICTION = "prediction"
AGENT_PNR = "pnr"
AGENT_KNOWLEDGE = "knowledge"
AGENT_CONVERSATION = "conversation"

# Error Codes
ERR_TIMEOUT = "TIMEOUT_ERROR"
ERR_ROUTING = "ROUTING_ERROR"
ERR_AGENT_EXECUTION = "AGENT_EXECUTION_ERROR"
ERR_GRAPH_EXECUTION = "GRAPH_EXECUTION_ERROR"
ERR_UNKNOWN = "UNKNOWN_ERROR"

# Node Names
NODE_CLASSIFIER = "ClassifierNode"
NODE_ROUTER = "RouterNode"
NODE_AGENT = "AgentNode"
NODE_MEMORY = "MemoryNode"
NODE_RESPONSE = "ResponseNode"
NODE_ERROR = "ErrorNode"

# Configuration Defaults
DEFAULT_TIMEOUT_SECS = 30.0
DEFAULT_RETRY_LIMIT = 3
GRAPH_NAME = "railyatra_orchestrator"
