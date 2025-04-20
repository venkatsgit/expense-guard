from db import get_db
import requests
from expense_classifier import ExpenseClassifier

class BatchClassifier:
    def __init__(self, user_id, file_id):
        self.user_id = user_id
        self.file_id = file_id
        self.processed_description = {}
        self.row_query_limit = 10
        self.unique_description_count = 0
        self.classifier = ExpenseClassifier(
    "config.yaml",
    classification_model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

    def process_table_data(self):

        descriptions = self.get_unique_descriptions()

        batch = []
        for desc in descriptions:
            if desc in self.processed_description:
                continue
            batch.append(desc)
            if len(batch) == self.row_query_limit:
                self.classify_and_store(batch)
                self.update_database(batch)
                batch = []

        if batch:
            self.classify_and_store(batch)
            self.update_database(batch)

    def get_unique_descriptions(self):
        query = """
            SELECT DISTINCT description 
            FROM expense_insights.expenses
            WHERE user_id = %s AND file_id = %s
            AND (category IS NULL OR category = '')
        """
        db, cursor = None, None
        try:
            db, cursor = get_db()
            cursor.execute(query, (self.user_id, self.file_id))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching descriptions: {e}")
            return []


    def classify_and_store(self,batch):
        try:
            results = self.classifier.classify(batch)
            print("results", results)
            for desc, result in zip(batch, results):
                self.processed_description[desc] = result
                print(f"Processed: {desc} -> {result}")

        except Exception as e:
            print(f"Error during classification: {e}")


    def update_database(self, batch):
        if not batch:
            return

        query = """
            UPDATE expense_insights.expenses 
            SET category = %s
            WHERE user_id = %s AND file_id = %s AND description = %s
            AND (category IS NULL OR category = '')
        """

        db, cursor = None, None
        try:
            db, cursor = get_db()
            update_values = [
                (self.processed_description[desc],
                 self.user_id, self.file_id, desc)
                for desc in batch
            ]
            cursor.executemany(query, update_values)
            db.commit()
        except Exception as e:
            print(f"Error updating database: {e}")
            db.rollback()
