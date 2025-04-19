from flask import Flask, request, jsonify
import requests
from db import init_db, close_db
from api import api_bp
import os


app = Flask(__name__)

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "mysql")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", 3306))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "remote_user")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "Str0ng@Pass123")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "expense_insights")

init_db(app)
app.register_blueprint(api_bp, url_prefix="/api")


@app.route('/health')
def home():
    return "Hello, Flask!"

# app.teardown_appcontext(close_db)


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
                #  temp user_id from google need to handle this
                request.user_id = response_json['id']
            else:
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

        except Exception as e:
            return jsonify({"error": "Invalid or missing token"}), 401


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8081, debug=False)
