from db import get_db
from flask import jsonify

def get_upload_history(user_id):

    try:
        db, cursor = get_db()
        query = """
            SELECT file_name, status, message, uploaded_at 
            FROM expense_insights.upload_history
            WHERE user_id = %s 
            ORDER BY uploaded_at DESC 
            LIMIT 100;
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        history = [
            {"file_name": row[0], "status": row[1],
                "message": row[2], "uploaded_at": row[3]}
            for row in result
        ]
        return jsonify({'status': 'success', 'data': history}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'internal server error'}), 500
