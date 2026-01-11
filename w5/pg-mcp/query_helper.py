#!/usr/bin/env python3
"""
Simple CLI to query PostgreSQL using natural language via the MCP server's components.
This is a standalone script that doesn't require MCP client setup.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pg_mcp.services.orchestrator import QueryOrchestrator
from pg_mcp.config.settings import Settings


async def query_database(question: str, return_type: str = "result"):
    """Query the database using natural language."""
    settings = Settings()
    orchestrator = QueryOrchestrator(settings)
    
    try:
        await orchestrator.initialize()
        result = await orchestrator.process_query(
            question=question,
            return_type=return_type
        )
        
        print("\n" + "="*80)
        print(f"Question: {question}")
        print("="*80)
        
        if result.get("success"):
            print(f"\n✓ Generated SQL:\n{result['generated_sql']}\n")
            
            if return_type == "result" and "data" in result:
                data = result["data"]
                print(f"Rows returned: {data['row_count']}")
                print(f"Execution time: {data['execution_time']:.3f}s")
                print(f"\nResults:")
                print("-" * 80)
                
                # Print column headers
                if data['columns']:
                    print(" | ".join(data['columns']))
                    print("-" * 80)
                
                # Print rows
                for row in data['rows'][:10]:  # Limit to first 10 rows
                    print(" | ".join(str(val) for val in row))
                
                if data['row_count'] > 10:
                    print(f"\n... and {data['row_count'] - 10} more rows")
            
            if "confidence" in result:
                print(f"\nConfidence: {result['confidence']}%")
        else:
            print(f"\n✗ Error: {result.get('error', {}).get('message', 'Unknown error')}")
        
        print("="*80 + "\n")
        
    finally:
        await orchestrator.cleanup()


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python query_helper.py 'your natural language question'")
        print("\nExamples:")
        print("  python query_helper.py 'How many users are there?'")
        print("  python query_helper.py 'Show me the most recent blog posts'")
        print("  python query_helper.py 'What are the top 5 most popular tags?'")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    await query_database(question)


if __name__ == "__main__":
    asyncio.run(main())
