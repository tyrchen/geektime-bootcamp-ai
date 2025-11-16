"""Natural Language to SQL conversion service using OpenAI."""

from openai import AsyncOpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class NaturalLanguageToSQLService:
    """Service for converting natural language queries to SQL using OpenAI."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Cost-effective model for SQL generation

    def _build_prompt(
        self, user_prompt: str, metadata: dict
    ) -> list[dict[str, str]]:
        """Build the prompt for OpenAI with database metadata context.

        Args:
            user_prompt: Natural language query from user
            metadata: Database schema metadata dictionary

        Returns:
            List of messages for OpenAI chat completion
        """
        # Build schema context
        schema_context = []
        for table in metadata.get("tables", []):
            columns_info = []
            for col in table.get("columns", []):
                col_desc = f"  - {col['name']} ({col['dataType']})"
                if col.get("primaryKey"):
                    col_desc += " PRIMARY KEY"
                if not col.get("nullable", True):
                    col_desc += " NOT NULL"
                if col.get("unique"):
                    col_desc += " UNIQUE"
                columns_info.append(col_desc)

            row_count = table.get("rowCount", "unknown")
            table_info = f"Table: {table['schemaName']}.{table['name']} ({row_count} rows)\n"
            table_info += "\n".join(columns_info)
            schema_context.append(table_info)

        for view in metadata.get("views", []):
            columns_info = [f"  - {col['name']} ({col['dataType']})" for col in view.get("columns", [])]
            view_info = f"View: {view['schemaName']}.{view['name']}\n"
            view_info += "\n".join(columns_info)
            schema_context.append(view_info)

        schema_text = "\n\n".join(schema_context)

        system_message = f"""You are an expert SQL query generator for PostgreSQL databases.

Database Schema:
{schema_text}

Rules:
1. Generate ONLY SELECT queries (no INSERT/UPDATE/DELETE/DROP)
2. Always include LIMIT clause (max 1000 rows)
3. Use proper schema qualification (schema.table)
4. Return valid PostgreSQL syntax
5. Handle both English and Chinese natural language
6. Be concise - return just the SQL query

Output format:
Return ONLY the SQL query, nothing else. No explanations, no markdown, just the SQL."""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

    async def generate_sql(
        self, user_prompt: str, metadata: dict
    ) -> dict[str, str]:
        """Convert natural language to SQL query.

        Args:
            user_prompt: Natural language query
            metadata: Database schema metadata dictionary

        Returns:
            Dict with 'sql' and 'explanation' keys

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            messages = self._build_prompt(user_prompt, metadata)

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=500,
            )

            generated_sql = response.choices[0].message.content.strip()

            # Clean up the response (remove markdown code blocks if present)
            if generated_sql.startswith("```sql"):
                generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
            elif generated_sql.startswith("```"):
                generated_sql = generated_sql.replace("```", "").strip()

            # Generate explanation
            explanation = f"Generated SQL from: {user_prompt}"

            logger.info(f"Generated SQL for prompt: {user_prompt[:50]}...")

            return {"sql": generated_sql, "explanation": explanation}

        except Exception as e:
            logger.error(f"Failed to generate SQL: {str(e)}")
            raise Exception(f"Failed to generate SQL: {str(e)}")


# Global instance
nl2sql_service = NaturalLanguageToSQLService()
