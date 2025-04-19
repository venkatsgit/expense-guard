from flask import g
from flask_mysqldb import MySQL

mysql = MySQL()  # MySQL instance

def init_db(app):
    mysql.init_app(app)

def get_db():
    if "db" not in g:
        g.db = mysql.connection
        g.cursor = g.db.cursor()
    return g.db, g.cursor

def is_connection_alive(db):
    """Check if MySQL connection is still alive"""
    try:
        db.ping(reconnect=True)  # ✅ Try pinging MySQL server
        return True
    except Exception:
        return False

def close_db(exception=None):
    """Close the database connection if it's open"""
    cursor = g.pop("cursor", None)
    db = g.pop("db", None)

    if cursor:
        try:
            cursor.close()  # ✅ Close cursor safely
        except Exception as e:
            print(f"Cursor close error: {e}")

    if db and is_connection_alive(db):  # ✅ Check before closing
        try:
            db.close()  # ✅ Close only if alive
        except Exception as e:
            print(f"DB close error: {e}")