import json
import requests
from typing import List, Dict, Any, Optional, Union
# Import the FewShotManager class from your module
from few_shot_manager import FewShotManager
from query_executer import QueryExecuter


class NL2SQLConverter:
    """
    Converts natural language queries to SQL using Google's Generative AI API
    with few-shot learning examples.
    """

    def __init__(
            self,
            api_key: str,
            model: str = "gemini-2.0-flash",
            db_type: str = "mysql",
            table_info: Dict[str, Any] = None,
            project_config: Dict[str, Any] = None,
            project_name: str = None,
            user_rules: List[str] = None,
            max_examples: int = 3
    ):
        """
        Initialize the NL2SQL converter

        Args:
            api_key: Google API key
            model: Google Generative AI model to use
            db_type: Database type ('mysql' or 'sqlserver')
            table_info: Dictionary containing table schema information
            user_rules: List of rules to apply to SQL generation
            max_examples: Maximum number of similar examples to include
        """
        self.api_key = api_key
        self.model = model
        self.db_type = db_type
        self.table_info = table_info or {}
        self.project_config = project_config or {}
        self.user_rules = user_rules or []
        self.max_examples = max_examples
        self.project_name = project_name
        self.few_shot_manager = FewShotManager(
            db_type=db_type)
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def set_table_info(self, table_info: Dict[str, Any]) -> None:
        """Set or update the table schema information"""
        self.table_info = table_info

    def set_rules(self, rules: List[str]) -> None:
        """Set or update the rules for SQL generation"""
        self.user_rules = rules

    def _build_prompt(self, query: str, user_id: Optional[int] = None) -> str:
        """
        Build the prompt for the API with table information, user rules,
        and similar examples.

        Args:
            query: Natural language query
            user_id: User ID for filtering (if applicable)

        Returns:
            Formatted prompt string
        """
        # Get similar examples using the FewShotManager
        similar_examples = self.few_shot_manager.get_similar_examples(
            query, n_results=self.max_examples
        )

        # Format the examples section
        examples_text = ""
        if similar_examples:
            examples_text = "**Similar Examples:**\n"
            for i, example in enumerate(similar_examples):
                examples_text += f"Example {i + 1}:\n"
                examples_text += f"Question: \"{example['prompt']}\"\n"
                examples_text += f"SQL: ```{example['sql']}```\n\n"

        # Format table information
        table_info_text = ""
        if self.table_info:
            table_info_text = "**TABLE INFORMATION:**\n"
            for table_name, columns in self.table_info.items():
                table_info_text += f"Table: `{table_name}`\n"
                if isinstance(columns, list):
                    table_info_text += "- Columns: " + \
                        ", ".join([f"`{col}`" for col in columns]) + "\n"
                elif isinstance(columns, dict):
                    table_info_text += "- Columns:\n"
                    for col_name, col_desc in columns.items():
                        table_info_text += f"  - `{col_name}`: {col_desc}\n"

        # Format rules
        rules_text = ""
        if self.user_rules:
            rules_text = "**Rules (STRICTLY FOLLOW):**\n"
            for rule in self.user_rules:
                rules_text += f"- {rule}\n"

        # Build the complete prompt
        user_filter = ""
        if 'is_user_filter_needed' in self.project_config and self.project_config['is_user_filter_needed']:
            user_filter = f"for user_id={user_id}" if user_id is not None else ""

        prompt = f"""
        You are an AI assistant. Convert natural language questions into SQL queries.

        {table_info_text}

        **Question:** "{query} {user_filter}?"

        {rules_text}

        {examples_text}

        **Response Format:**
        - Valid query → {{"query":"SQL_QUERY"}}
        - Invalid question → {{"error_message":"Error message"}}

        Now, generate the response:
        """

        return prompt

    def convert_to_sql(self, query: str, user_id: Optional[int] = None) -> Dict[str, str]:
        """
        Convert natural language query to SQL

        Args:
            query: Natural language query
            user_id: User ID for filtering (if applicable)

        Returns:
            Dictionary with either 'query' or 'error_message' key
        """
        # Build the prompt
        prompt = self._build_prompt(query, user_id)

        # Prepare the API request
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        # Call the API
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()  # Raise exception for HTTP errors

            result = response.json()

            # Extract the response text
            if (
                    'candidates' in result and
                    result['candidates'] and
                    'content' in result['candidates'][0] and
                    'parts' in result['candidates'][0]['content'] and
                    result['candidates'][0]['content']['parts'] and
                    'text' in result['candidates'][0]['content']['parts'][0]
            ):
                response_text = result['candidates'][0]['content']['parts'][0]['text'].strip(
                )

                # Try to parse the JSON response
                try:
                    response_text = response_text.replace("```json", "").replace(
                        "```", "").replace("json", "").strip()
                    parsed_response = json.loads(response_text)

                    # Check if we have a valid response format
                    if 'query' in parsed_response:
                        return {"query": parsed_response['query']}
                    elif 'error_message' in parsed_response:
                        return {"error_message": parsed_response['error_message']}
                    else:
                        # Try to extract SQL if the response wasn't in the expected format
                        if '```sql' in response_text:
                            sql_start = response_text.find('```sql') + 6
                            sql_end = response_text.find('```', sql_start)
                            if sql_start > 6 and sql_end > sql_start:
                                sql = response_text[sql_start:sql_end].strip()
                                return {"query": sql}

                        return {"error_message": "Invalid response format from model"}
                except json.JSONDecodeError:
                    # Handle case where model didn't return proper JSON
                    return {"error_message": "Failed to parse model response as JSON"}

            return {"error_message": "Invalid or empty response from model"}

        except requests.RequestException as e:
            return {"error_message": f"API request error: {str(e)}"}


# Example usage
if __name__ == "__main__":
    # Configuration
    API_KEY = "AIzaSyAetG3Sl0UVG3InmMLz0DWAPFJrG41sBJg"

    project_name = "sales"
    table_info = {}
    with open('table_configurations.json', 'r') as table_configuration:
        table_configuration_json = json.load(table_configuration)
        project_config = {}
        for data in table_configuration_json:
            if 'project_name' in data and data['project_name'] == project_name:
                project_config = data
                break

        if len(project_config) <= 0:
            print("project not found")
    rules = project_config['rules']

    # Initialize converter
    converter = NL2SQLConverter(
        api_key=API_KEY,
        table_info=project_config['table_info'],
        user_rules=rules,
        project_config=project_config,
        project_name=project_name,
        db_type=project_config['db_type']
    )

    # First populate the example database if not already done
    # (Assuming you've already run populate_examples() previously)

    # Test queries
    test_queries = [
        "What is the total sales for the group in local currency?"
    ]

    # Test the converter
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = converter.convert_to_sql(query, user_id=1)

        if "query" in result:
            print(f"SQL: {result['query']}")
        else:
            print(f"Error: {result['error_message']}")

        if "query" in result:
            db_config = project_config['db_connection_config']
            executor = QueryExecuter(
                db_type=project_config['db_type'], query=result['query'], **db_config)
            result = executor.execute()
            print(result)
