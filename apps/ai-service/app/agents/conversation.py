import logging
from app.agents.base import BaseAgent
from app.prompts.system import SYSTEM_PERSONA

logger = logging.getLogger("ai-service.agents.conversation")

CONVERSATION_PROMPT = SYSTEM_PERSONA + """
You are the Conversation Agent. You handle general chit-chat, greetings, queries about yourself, and general inquiries that do not involve active travel planning.
Keep your response concise, polite, and helpful, but gently guide the user back to how you can help them with railway travel intelligence.
"""

class ConversationAgent(BaseAgent):
    """
    Agent responsible for social interaction, greetings, and casual questions.
    """
    def __init__(self):
        super().__init__(
            name="ConversationAgent",
            system_prompt=CONVERSATION_PROMPT
        )
