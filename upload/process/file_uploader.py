from flask import jsonify
from db import get_db
import pandas as pd
import datetime
import requests


class FileUploader:

    def __init__(self, file, file_name, file_meta_data, user_id):
        self.file = file
        self.file_name = file_name
        self.file_meta_data = file_meta_data
        self.user_id = user_id
        self.file_id = -1

    def validate_and_insert(self):

        try:
            file = self.file
            file_name = self.file_name
            file_meta_data = self.file_meta_data
            user_id = self.user_id

            required_headers = file_meta_data['required_headers']
            data_frame = pd.read_csv(file)

            data_frame.columns = data_frame.columns.str.lower()

            if 'header_mapping' in file_meta_data:
                self.header_mapping(data_frame, file_meta_data)

            missing_columns = [
                col for col in required_headers if col not in data_frame.columns]
            if missing_columns:
                self.insert_upload_history(
                    "FAILED", "Missing columns: " + ', '.join(missing_columns))
                return jsonify({'status': 'error', 'message': 'Missing columns: ' + ', '.join(missing_columns)}), 400

            data_frame = data_frame[required_headers].dropna()

            # common fileds

            data_frame["user_id"] = user_id
            data_frame["created_at"] = datetime.datetime.now().replace(
                microsecond=0)

            if 'empty_fields_to_add' in file_meta_data:
                self.add_empty_fields(data_frame, file_meta_data)
            return self.insert_to_db(data_frame, file_meta_data)

        except Exception as e:
            print(e)
            self.insert_upload_history("FAILED", "internal server error")
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    def header_mapping(self, data_frame, file_meta_data):
        header_mapping = file_meta_data['header_mapping']
        data_frame.rename(columns=header_mapping,
                          inplace=True)

    def add_empty_fields(self, data_frame, file_meta_data):
        empty_fields_to_add = file_meta_data['empty_fields_to_add']
        for field in empty_fields_to_add:
            data_frame[field] = ""

    def insert_to_db(self, data_frame, file_meta_data):

        try:
            db, cursor = get_db()
            sql_table_name = file_meta_data['sql_table_name']
            sql_schema_name = file_meta_data['sql_schema_name']
            sql_column_names = file_meta_data['sql_column_names']
            upload_history_response = self.insert_upload_history(
                "PROCESSING", "upload in progress")
            if upload_history_response.json['status'] == "error":
                return jsonify({'status': 'error', 'message': 'Upload error'}), 500
            file_id = upload_history_response.json['history_id']
            data_frame['file_id'] = self.file_id
            insert_query = f"""
                INSERT IGNORE INTO {sql_schema_name}.{sql_table_name} ({', '.join(sql_column_names)}) 
                VALUES ({', '.join(['%s'] * len(sql_column_names))})
            """
            data_frame = data_frame[sql_column_names]
            data_to_insert = [tuple(row) for row in data_frame.to_numpy()]
            cursor.executemany(insert_query, data_to_insert)

            db.commit()
            self.update_upload_history("SUCCESS", "uploaded successfully")
            if 'model_processing' in file_meta_data:
                self.call_model_api()
            # cursor.close()
            return jsonify({'status': 'success', 'message': 'file uploaded successfully!'}), 200
        except Exception as e:
            print(e)
            self.insert_upload_history("FAILED", "internal server error")
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    def insert_upload_history(self, status, message):

        try:
            user_id = self.user_id
            file_name = self.file_name

            db, cursor = get_db()
            sql_columns = ["user_id", "file_name",
                           "status", "message", "uploaded_at"]
            insert_query = f"""
                INSERT INTO expense_insights.upload_history ({', '.join(sql_columns)}) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (user_id, file_name, status,
                                          message, datetime.datetime.now().replace(microsecond=0)))
            cursor.execute("SELECT LAST_INSERT_ID();")

            file_id = cursor.fetchone()[0]
            self.file_id = file_id
            db.commit()
            return jsonify({'status': 'success', 'history_id': file_id})

        except Exception as e:
            print(e)
            return jsonify({'status': 'error', 'message': 'Internal server error'})

    def update_upload_history(self, status, message):

        try:
            db, cursor = get_db()
            update_query = """
                UPDATE expense_insights.upload_history
                SET status = %s, message = %s
                WHERE id = %s;
            """
            cursor.execute(
                update_query, (status, message, self.file_id))
            db.commit()
        except Exception as e:
            print(e)

    def call_model_api(self):
        try:
            file_meta_data = self.file_meta_data
            model_processing = file_meta_data['model_processing'][0]
            url = model_processing['url']
            payload = {
                'user_id': self.user_id,
                'table_name': file_meta_data['sql_table_name'],
                'schema_name': file_meta_data['sql_schema_name'],
                'file_id': self.file_id
            }
            headers = {
                "auth": ""
            }
            response = requests.post(url=url, json=payload)

            if response.status_code == 200:
                print('classifier process started')
            else:
                print("error")
        except Exception as e:
            print(e)


