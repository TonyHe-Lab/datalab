"""
Prompt engineering for medical diagnostic RAG chat.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PromptEngineer:
    """Engineer prompts for medical diagnostic assistance."""

    def __init__(
        self,
        system_prompt: str = None,
        context_limit: int = 5,
    ):
        """
        Initialize prompt engineer.

        Args:
            system_prompt: Custom system prompt
            context_limit: Maximum number of similar cases to include
        """
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.context_limit = context_limit

    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt for medical diagnostics.

        Returns:
            Default system prompt
        """
        return """You are an expert medical equipment diagnostic assistant specializing in maintenance and repair.

Your role:
- Analyze maintenance work orders and diagnostic queries
- Provide evidence-based recommendations using similar historical cases
- Help identify root causes and suggest resolution steps
- Always include source attribution for recommendations

Guidelines:
- Base your recommendations on the provided context (similar historical cases)
- If no relevant context is available, state that limitations
- Include confidence levels for recommendations
- Suggest specific, actionable steps
- Reference the notification IDs of similar cases when applicable
- Maintain professional and technical language

Safety:
- Always recommend consulting official documentation and manufacturer guidelines
- Do not provide medical advice that could affect patient safety
- Emphasize the need for qualified technicians for repairs"""

    def format_context_for_prompt(
        self,
        search_results: List[Dict],
    ) -> str:
        """
        Format search results into context for the prompt.

        Args:
            search_results: List of search results from hybrid search

        Returns:
            Formatted context string
        """
        if not search_results:
            return "No relevant historical cases found in the database."

        context_parts = []

        context_parts.append("SIMILAR HISTORICAL CASES:\n")

        for idx, result in enumerate(search_results[: self.context_limit], start=1):
            context_parts.append(f"\n--- Case {idx} ---")
            context_parts.append(f"Notification ID: {result.get('noti_id', 'N/A')}")
            context_parts.append(f"Equipment ID: {result.get('equipment_id', 'N/A')}")
            context_parts.append(f"Date: {result.get('date', 'N/A')}")

            # Include text or snippet
            text = result.get("text") or result.get("snippet", "N/A")
            context_parts.append(f"Issue Description: {text}")

            # Include similarity if available
            if "similarity" in result:
                context_parts.append(f"Similarity Score: {result['similarity']:.3f}")
            if "relevance" in result:
                context_parts.append(f"Relevance Score: {result['relevance']:.3f}")

        return "\n".join(context_parts)

    def build_rag_prompt(
        self,
        user_query: str,
        context: str,
    ) -> str:
        """
        Build complete RAG prompt with user query and retrieved context.

        Args:
            user_query: User's diagnostic query
            context: Retrieved context from search

        Returns:
            Complete prompt for AI generation
        """
        prompt = f"""{self.system_prompt}

-----

{context}

-----

USER QUERY:
{user_query}

-----

Please provide a comprehensive analysis with:
1. Summary of the issue based on similar cases
2. Possible root causes
3. Recommended resolution steps
4. Additional considerations or warnings
5. Source attribution (reference the similar cases above)"""

        return prompt

    def build_chat_prompt(
        self,
        user_query: str,
        conversation_history: List[Dict[str, str]],
        context: str,
    ) -> str:
        """
        Build chat prompt with conversation history.

        Args:
            user_query: Current user query
            conversation_history: List of previous messages
            context: Retrieved context from search

        Returns:
            Complete chat prompt
        """
        # Build conversation history
        history_parts = []
        for msg in conversation_history[-5:]:  # Limit to last 5 messages
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            history_parts.append(f"{role}: {content}")

        history_str = (
            "\n".join(history_parts) if history_parts else "No previous conversation."
        )

        prompt = f"""{self.system_prompt}

-----

CONVERSATION HISTORY:
{history_str}

-----

{context}

-----

CURRENT USER QUERY:
{user_query}

-----

Please provide a helpful, contextual response based on the conversation history and similar cases above."""

        return prompt

    def validate_prompt(self, prompt: str, max_length: int = 8000) -> bool:
        """
        Validate prompt length and content.

        Args:
            prompt: Prompt to validate
            max_length: Maximum allowed length in characters

        Returns:
            True if valid, False otherwise
        """
        if not prompt or len(prompt.strip()) == 0:
            logger.warning("Empty prompt provided")
            return False

        if len(prompt) > max_length:
            logger.warning(f"Prompt too long: {len(prompt)} > {max_length}")
            return False

        # Check for potential prompt injection patterns
        dangerous_patterns = [
            "SYSTEM:",
            "INSTRUCTION:",
            "HUMAN:",
            "ASSISTANT:",
        ]

        for pattern in dangerous_patterns:
            if pattern in prompt.upper() and pattern not in self.system_prompt.upper():
                logger.warning(f"Potential prompt injection detected: {pattern}")
                return False

        return True

    def sanitize_query(self, query: str) -> str:
        """
        Sanitize user query to prevent prompt injection.

        Args:
            query: User query to sanitize

        Returns:
            Sanitized query
        """
        # Remove common prompt injection patterns
        sanitized = query

        dangerous_prefixes = [
            "ignore all previous instructions",
            "ignore above",
            "disregard everything",
            "forget everything",
        ]

        for prefix in dangerous_prefixes:
            if sanitized.lower().startswith(prefix.lower()):
                sanitized = "[REDIRECTED: User attempting prompt injection]"
                logger.warning(f"Prompt injection attempt detected: {prefix}")
                break

        return sanitized[:2000]  # Limit query length
