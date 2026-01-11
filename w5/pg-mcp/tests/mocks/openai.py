"""Mock OpenAI client for testing."""

from typing import Any
from unittest.mock import AsyncMock


class MockChatCompletion:
    """Mock OpenAI ChatCompletion response."""

    def __init__(self, content: str, tokens_used: int = 100):
        """Initialize mock completion.

        Args:
            content: Response content (SQL query).
            tokens_used: Number of tokens used.
        """
        self.choices = [
            type(
                "Choice",
                (),
                {
                    "message": type("Message", (), {"content": content})(),
                    "finish_reason": "stop",
                },
            )()
        ]
        self.usage = type(
            "Usage",
            (),
            {
                "prompt_tokens": tokens_used // 2,
                "completion_tokens": tokens_used // 2,
                "total_tokens": tokens_used,
            },
        )()

    def model_dump(self) -> dict[str, Any]:
        """Return dict representation."""
        return {
            "choices": [
                {
                    "message": {"content": self.choices[0].message.content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
            },
        }


class MockChatCompletions:
    """Mock OpenAI chat.completions API."""

    def __init__(self, sql_response: str = "SELECT 1", tokens_used: int = 100):
        """Initialize mock completions API.

        Args:
            sql_response: SQL query to return.
            tokens_used: Number of tokens to report.
        """
        self.sql_response = sql_response
        self.tokens_used = tokens_used
        self.call_count = 0
        self.last_messages: list[dict] | None = None
        self.last_model: str | None = None
        self._sql_sequence: list[str] = []

    def set_mock_sql(self, sql: str):
        """Set SQL to return from next create() call.

        Args:
            sql: SQL query string to return.
        """
        self.sql_response = sql
        self._sql_sequence = []

    def set_mock_sql_sequence(self, sql_list: list[str]):
        """Set sequence of SQL to return from create() calls.

        Args:
            sql_list: List of SQL strings to return in order.
        """
        self._sql_sequence = sql_list.copy()

    async def create(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs,
    ) -> MockChatCompletion:
        """Mock create completion.

        Args:
            model: Model name.
            messages: Chat messages.
            temperature: Sampling temperature.
            max_tokens: Max tokens to generate.
            **kwargs: Additional arguments.

        Returns:
            MockChatCompletion instance.
        """
        self.call_count += 1
        self.last_messages = messages
        self.last_model = model

        # Get SQL from sequence or use default
        if self._sql_sequence:
            sql = self._sql_sequence.pop(0)
        else:
            sql = self.sql_response

        # Wrap in code block for proper extraction
        content = f"```sql\n{sql}\n```"
        return MockChatCompletion(content, self.tokens_used)


class MockChat:
    """Mock OpenAI chat API."""

    def __init__(self, sql_response: str = "SELECT 1", tokens_used: int = 100):
        """Initialize mock chat API.

        Args:
            sql_response: SQL query to return.
            tokens_used: Number of tokens to report.
        """
        self.completions = MockChatCompletions(sql_response, tokens_used)


class MockAsyncOpenAI:
    """Mock AsyncOpenAI client."""

    def __init__(self, sql_response: str = "SELECT 1", tokens_used: int = 100, **kwargs):
        """Initialize mock OpenAI client.

        Args:
            sql_response: SQL query to return from completions.
            tokens_used: Number of tokens to report.
            **kwargs: Additional arguments (api_key, timeout, etc).
        """
        self.chat = MockChat(sql_response, tokens_used)
        self.api_key = kwargs.get("api_key", "sk-test")
        self.timeout = kwargs.get("timeout", 30.0)

    def set_mock_sql(self, sql: str):
        """Set SQL to return from next create() call.

        Args:
            sql: SQL query string to return.
        """
        self.chat.completions.set_mock_sql(sql)

    def set_mock_sql_sequence(self, sql_list: list[str]):
        """Set sequence of SQL to return from create() calls.

        Args:
            sql_list: List of SQL strings to return in order.
        """
        self.chat.completions.set_mock_sql_sequence(sql_list)


def create_mock_openai_client(
    sql_response: str = "SELECT 1",
    tokens_used: int = 100,
) -> MockAsyncOpenAI:
    """Create a mock AsyncOpenAI client.

    Args:
        sql_response: SQL query to return from completions.
        tokens_used: Number of tokens to report.

    Returns:
        MockAsyncOpenAI instance.

    Example:
        >>> client = create_mock_openai_client(sql_response="SELECT * FROM users")
        >>> response = await client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "List users"}]
        ... )
        >>> assert "SELECT" in response.choices[0].message.content
    """
    return MockAsyncOpenAI(sql_response=sql_response, tokens_used=tokens_used)
