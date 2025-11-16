"""Query result export service for CSV and JSON formats."""

import csv
import json
from io import StringIO
from typing import Any
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting query results to various formats."""

    def export_to_csv(self, columns: list[dict[str, str]], rows: list[dict[str, Any]]) -> str:
        """Export query results to CSV format.

        Args:
            columns: List of column definitions with 'name' and 'dataType'
            rows: List of row dictionaries

        Returns:
            CSV string
        """
        if not rows:
            return ""

        output = StringIO()
        column_names = [col["name"] for col in columns]
        writer = csv.DictWriter(output, fieldnames=column_names)

        # Write header
        writer.writeheader()

        # Write rows
        for row in rows:
            # Convert values to strings, handle None
            csv_row = {k: (str(v) if v is not None else "") for k, v in row.items()}
            writer.writerow(csv_row)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"Exported {len(rows)} rows to CSV")
        return csv_content

    def export_to_json(self, columns: list[dict[str, str]], rows: list[dict[str, Any]]) -> str:
        """Export query results to JSON format.

        Args:
            columns: List of column definitions with 'name' and 'dataType'
            rows: List of row dictionaries

        Returns:
            JSON string
        """
        # Build result structure
        result = {
            "columns": columns,
            "rows": rows,
            "rowCount": len(rows),
        }

        json_content = json.dumps(result, indent=2, default=str, ensure_ascii=False)

        logger.info(f"Exported {len(rows)} rows to JSON")
        return json_content


# Global instance
export_service = ExportService()
