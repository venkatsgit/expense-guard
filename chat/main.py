from flask import Flask, request, jsonify, g
from db import init_db, close_db
import os
import time
import requests
import json
from nl_sql_converter import NL2SQLConverter
from query_executer import QueryExecuter
from sql_nl_converter import SQL2NLConverter

app = Flask(__name__)

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "mysql")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", 3306))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "remote_user")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "Str0ng@Pass123")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "expense_insights")

project_name = os.getenv("PROJECT_NAME", "expense_insights")
API_KEY = os.getenv("API_KEY", "AIzaSyAetG3Sl0UVG3InmMLz0DWAPFJrG41sBJg")

init_db(app)


@app.route('/health')
def home():
    return "Hello, Flask!"

@app.before_request
def check_token():
    if request.endpoint != "health":
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401
            token = auth_header.split(" ")[1]
            headers = {
                "Authorization": f"Bearer {token}"
            }
            response = requests.get(
                "https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
            if response.status_code == 200:
                response_json = response.json()
                g.user_id = response_json['id']
                g.email = response_json['email']
            else:
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

        except Exception as e:
            return jsonify({"error": "Invalid or missing token"}), 401


@app.route('/chatbot', methods=['POST'])
def chat():
    user_query = extract_user_query()
    if not user_query:
        return jsonify({'status': 'error', 'message': 'Invalid input'}), 400

    user_id = g.get('email', "")
    

    project_config = load_project_config(project_name)
    if not project_config:
        print("Project not found")
        return jsonify({'status': 'error', 'message': 'Project not found'}), 404

    rules = project_config['rules']

    converter = initialize_converter(project_config, rules)
    sql_nl_converter = initialize_nl_converter(project_config, rules)

    timings = {}

    # Timing: convert_to_sql
    t0 = time.time()
    result = converter.convert_to_sql(user_query, user_id=user_id)
    timings['convert_to_sql'] = time.time() - t0

    if "query" not in result:
        print(f"Error: {result['error_message']}",flush=True)
        return jsonify({'status': 'error', 'message': result['error_message']}), 500

    print(f"SQL: {result['query']}",flush=True)

    # Timing: execute_query
    t1 = time.time()
    query_result = execute_query(project_config, result['query'])
    timings['execute_query'] = time.time() - t1

    print(f"query_result: {query_result}",flush=True)

    # Timing: convert_to_nl
    t2 = time.time()
    query_text = sql_nl_converter.convert_to_nl(user_query, query_result)
    timings['convert_to_nl'] = time.time() - t2

    # Print all timings together
    print(
        f"Execution Times (s) -> SQL Conversion: {timings['convert_to_sql']:.4f}, "
        f"Query Execution: {timings['execute_query']:.4f}, "
        f"NL Conversion: {timings['convert_to_nl']:.4f}",
        flush=True
    )

    return jsonify({'status': 'success', 'answer': query_text}), 200


def extract_user_query():
    if request.json and request.json.get('question'):
        return request.json['question']
    return None


def load_project_config(project_name):
    try:
        with open('table_configurations.json', 'r') as table_configuration:
            table_configuration_json = json.load(table_configuration)
            for data in table_configuration_json:
                if data.get('project_name') == project_name:
                    return data
    except Exception as e:
        print(f"Error loading project config: {e}")
    return None


def initialize_converter(config, rules):
    return NL2SQLConverter(
        api_key=API_KEY,
        table_info=config['table_info'],
        user_rules=rules,
        project_config=config,
        project_name=config['project_name'],
        db_type=config['db_type']
    )


def initialize_nl_converter(config, rules):
    return SQL2NLConverter(
        api_key=API_KEY,
        table_info=config['table_info'],
        db_type=config['db_type'],
        project_config=config,
    )

def execute_query(config, sql_query):
    db_config = config['db_connection_config']
    executor = QueryExecuter(
        db_type=config['db_type'],
        query=sql_query,
        **db_config
    )
    return executor.execute()

app.teardown_appcontext(close_db)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8083, debug=False)
