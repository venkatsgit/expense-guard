import requests
from typing import List, Dict, Any
from flask import Flask, g

# Initialize Flask app
app = Flask(__name__)

class SQL2NLConverter:
    """
    SQL to Natural Language Converter
    This class converts structured SQL query results into a human-readable summary using  Google's Generative AI API.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", db_type: str = "mysql",
                 table_info: Dict[str, Any] = None,   project_config: Dict[str, Any] = None):
        """
        Initialize the SQL2NLConverter class with API key and settings.

        Args:
            api_key (str): API key for the generative AI model.
            model (str): Model name for AI processing (default: "gemini-2.0-flash").
            db_type (str): Type of database (default: "mysql").
            table_info (dict): Optional dictionary containing database schema details.
        """
        self.api_key = api_key
        self.model = model
        self.db_type = db_type
        self.table_info = table_info or {}
        self.project_config = project_config or {}
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def _build_nl_prompt(self, question: str, query_response: Any) -> str:
        """
        Construct a natural language prompt for the AI model to convert SQL response.

        Args:
            question (str): The user's natural language question.
            query_response (Any): The raw response from the SQL query.

        Returns:
            str: A formatted AI prompt for natural language conversion.
        """

        # AI instructions to prevent exposure of SQL structure and maintain natural responses
        instructions_list = self.project_config.get("SqlToNlRules", [])
        instructions = "\n".join(f"- {rule}" for rule in instructions_list)

        # Constructing table information if available
        table_description = ""
        if self.table_info:
            table_description = "**TABLE INFORMATION:**\n"
            for table_name, columns in self.table_info.items():
                table_description += f"Table: `{table_name}`\n"
                if isinstance(columns, list):
                    table_description += "- Columns: " + ", ".join([f"`{col}`" for col in columns]) + "\n"
                elif isinstance(columns, dict):
                    table_description += "- Columns:\n"
                    for col_name, col_desc in columns.items():
                        table_description += f"  - `{col_name}`: {col_desc}\n"

        # Construct the final AI prompt
        prompt = f"""
            You are an AI assistant. Convert the database response into a natural, human-readable summary.
        
            {table_description}
        
            {instructions}
        
            ### Input:
            - **User Question:** {question}
            - **Database Response:** {query_response}
        
            Now, generate the response:
        """
        return prompt

    def convert_to_nl(self, query: str, query_response: Any) -> Dict[str, str]:
        """
        Convert a SQL query result into a human-readable natural language summary.

        Args:
            query (str): The SQL query executed.
            query_response (Any): The response returned by the database.

        Returns:
            Dict[str, str]: A dictionary with the generated natural language response.
        """
        prompt = self._build_nl_prompt(query, query_response)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()

            candidates = data.get('candidates', [])
            if not candidates:
                return {"error_message": "No valid response from AI."}

            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                return {"error_message": "Empty AI response."}

            query_text = parts[0].get('text', "").strip()
            return {"query_text": query_text} if query_text else {"error_message": "No generated text."}

        except requests.RequestException as e:
            return {"error_message": f"API request error: {str(e)}"}
