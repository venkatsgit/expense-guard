import os
from fastapi import FastAPI, HTTPException
import urllib.parse
from pydantic import BaseModel
import re
import uvicorn
from huggingface_hub import InferenceClient
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import config

app = FastAPI()

# Database connection details
db_password = urllib.parse.quote(config.db_password)


class QuestionRequest(BaseModel):
    question: str
    userID: str


# Initialize SQL Database
try:
    db = SQLDatabase.from_uri(f"mysql+pymysql://{config.db_user}:{db_password}@{config.db_host}/{config.db_name}",
                              include_tables=config.select_table)
    print("Database connected successfully.")
except SQLAlchemyError as e:
    print(f" Database connection error: {e}")
    exit()

# Initialize Hugging Face Inference Client
client = InferenceClient("https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
                         token=config.HUGGINGFACEHUB_API_TOKEN)


# Function to generate a valid SQL query
def generate_sql_query(question, userID):
    try:
        schema_info = """
           The database has a table named 'expenses' with the following columns:
           - id (integer, primary key)
           - category (varchar)
           - expense (decimal)
           - date (date)

           Ensure the generated SQL query replaces NULL values with 0 using COALESCE.
           Generate ONLY the SQL query based on this table.
           """

        # prompt = f"Generate a MySQL query based on the following question:\n\nQuestion: {question}\n\nSQL Query:"

        prompt = f"{schema_info}\n\n{question}"
        response = client.text_generation(prompt)
        response = response.strip()

        # Extract only the SQL query using regex
        sql_match = re.search(r"```sql\s+(.*?)\s+```", response, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
        else:
            sql_query = response

        # Basic validation
        if not sql_query.lower().startswith("select"):
            raise ValueError("Generated response is not a valid SQL query.")

        user_condition = f"user_id = '{userID}'"

        if "where" in sql_query.lower():
            sql_query = re.sub(r"(where\s+)", r"\1" + user_condition + " AND ", sql_query, flags=re.IGNORECASE)
        else:
            sql_query = sql_query.rstrip(";") + f" WHERE {user_condition};"
        print(sql_query)
        return sql_query
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None


# Function to execute SQL query
def execute_sql_query(query):
    execute_query = QuerySQLDatabaseTool(db=db)
    try:
        result = execute_query.invoke(query)
        return result
    except SQLAlchemyError as e:
        print(f"Error executing SQL query: {e}")
        return None


# Wrap Hugging Face client in a LangChain Runnable
def query_huggingface(input_text):
    """Ensure the input is a plain string before sending it to Hugging Face."""
    if not isinstance(input_text, str):
        input_text = str(input_text)
    return client.text_generation(input_text)


llm_runnable = RunnableLambda(query_huggingface)

# Answer rephrasing prompt
answer_prompt = PromptTemplate.from_template(
     """You are a helpful assistant. Given the following user question, SQL query, and SQL result, provide only the final answer with explanations.

    Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    
    Answer:
    """
)


# LangChain pipeline for query execution and rephrasing
def process_question(question, userID):
    query = generate_sql_query(question, userID)
    if query:
        print(f"Generated SQL Query:\n{query}")
        result = execute_sql_query(query)

        if result:
            rephrase_answer = answer_prompt | llm_runnable | StrOutputParser()
            answer = rephrase_answer.invoke({"question": question, "query": query, "result": result})
            return answer
        else:
            return "SQL execution failed."
    else:
        return "Failed to generate a valid SQL query."


@app.post("/chatbot")
def chatbot_endpoint(request: QuestionRequest):
    answer = process_question(request.question, request.userID)
    print({"userID": request.userID, "question": request.question, "answer": answer})
    return {"userID": request.userID, "question": request.question, "answer": answer}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083)