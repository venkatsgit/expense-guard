from flask import g
from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    mysql.init_app(app)

def get_db():
    if "db" not in g:
        g.db = mysql.connection
        g.cursor = g.db.cursor()
    return g.db, g.cursor

def is_connection_alive(db):
    try:
        db.ping(reconnect=True) 
        return True
    except Exception:
        return False

def close_db(exception=None):
    cursor = g.pop("cursor", None)
    db = g.pop("db", None)

    if cursor:
        try:
            cursor.close()
        except Exception as e:
            print(f"Cursor close error: {e}")

    if db and is_connection_alive(db):
        try:
            db.close()
        except Exception as e:
            print(f"DB close error: {e}")