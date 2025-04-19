from flask import Flask, jsonify, request
from db import init_db, close_db
import os
import threading
from transformers import pipeline
from batch_classifier import BatchClassifier


app = Flask(__name__)
classifier = pipeline("zero-shot-classification",
                      model="facebook/bart-large-mnli")

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "127.0.0.1")
app.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT", 3306))
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "remote_user")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "Str0ng@Pass123")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "expense_insights")

init_db(app)


@app.route('/classify', methods=['POST'])
def classify_text():
    try:
        data = request.get_json()
        user_id = data['user_id']
        file_id = data['file_id']

        thread = threading.Thread(
            target=process_classification, args=(user_id, file_id))
        thread.start()

        return jsonify({'status': 'success', 'message': 'Processing started'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_classification(user_id, file_id):
    with app.app_context():
        try:
            expense_classifier = BatchClassifier(
                user_id, file_id)
            expense_classifier.process_table_data()
            print(
                f"Classification completed for user {user_id}, upload {file_id}")
        except Exception as e:
            print(f" Error during classification: {e}")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082, debug=False)
