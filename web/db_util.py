import mysql.connector
from datetime import datetime
import os


DB_CONFIG = {
    "host" : os.getenv("MYSQL_HOST", "host.docker.internal"),
    "user" : os.getenv("MYSQL_USER", "remote_user"),
    "password" : os.getenv("MYSQL_PASSWORD", "Str0ng@Pass123"),
    "database" :  os.getenv("MYSQL_DB", "expense_insights")
}

def get_db_conn():
        return mysql.connector.connect(**DB_CONFIG)

def update_user_db(user_info):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (user_info['email'],))
        result = cursor.fetchone()
        if result:
            cursor.execute("""
                UPDATE users
                SET last_login_at = %s
                WHERE email = %s
            """, (datetime.now(), user_info['email']))
        else:
            cursor.execute("""
                INSERT INTO users (name, email, created_at, last_login_at)
                VALUES(%s, %s, %s, %s)
            """, (user_info['name'], user_info['email'], datetime.now(), datetime.now()))

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()