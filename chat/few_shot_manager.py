import json
from typing import List, Dict, Any
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document


class FewShotManager:
    """
    Manages few-shot examples for NL to SQL conversion using ChromaDB and LangChain
    """

    def __init__(self, persist_directory: str = "./chroma_db", db_type: str = "mysql"):
        """
        Initialize the few-shot manager

        Args:
            persist_directory: Directory to store ChromaDB files
            db_type: Database type ('mysql' or 'sqlserver')
        """
        self.persist_directory = persist_directory
        self.db_type = db_type
        self.collection_name = f"sql_examples_{db_type}"

        # Initialize LangChain embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize LangChain Chroma vector store
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )

    def clear_examples(self) -> None:
        """
        Clears all documents from the vectorstore collection for the current db_type.
        """
        # Get all document IDs in this collection
        all_docs = self.vectorstore._collection.get()
        ids = all_docs.get("ids", [])

        if ids:
            self.vectorstore._collection.delete(ids=ids)
            print(f"Cleared {len(ids)} documents from collection '{self.collection_name}'")
        else:
            print(f"No documents to delete in collection '{self.collection_name}'")

    def add_examples(self, examples: List[Dict[str, str]]) -> None:
        """
        Add examples to the ChromaDB collection

        Args:
            examples: List of dictionaries with 'prompt' and 'sql' keys
        """

        documents = []
        metadatas = []

        for i, example in enumerate(examples):
            # Format the document with prompt and SQL clearly marked
            doc_text = f"User query: {example['prompt']}\nSQL: {example['sql']}"
            documents.append(Document(
                page_content=doc_text,
                metadata={
                    "prompt": example["prompt"],
                    "sql": example["sql"],
                    "db_type": self.db_type,
                    "example_id": i
                }
            ))

        # Add to LangChain vectorstore
        self.vectorstore.add_documents(documents)
        self.vectorstore.persist()

        print(
            f"Added {len(examples)} examples to ChromaDB collection '{self.collection_name}'")

    def get_similar_examples(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """
        Retrieve similar examples from ChromaDB

        Args:
            query: Natural language query
            n_results: Number of examples to retrieve

        Returns:
            List of dictionaries with 'prompt' and 'sql' keys
        """
        # Search for similar examples
        similar_docs = self.vectorstore.similarity_search(query, k=n_results)

        # Format results
        results = []
        for doc in similar_docs:
            results.append({
                "prompt": doc.metadata["prompt"],
                "sql": doc.metadata["sql"]
            })

        return results


def load_examples_from_config(config_path: str = "config.json") -> Dict[str, List[Dict[str, str]]]:
    """
    Load examples from the configuration file

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary with examples for each database type
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    return config

def populate_examples(config_path: str = "config.json") -> None:
    """
    Populate ChromaDB with examples from the configuration file

    Args:
        config_path: Path to the configuration file
    """
    # Load examples from configuration
    config_list = load_examples_from_config(config_path)
    # Populate examples for each database type
    for config_object in config_list:
        examples = config_object.get('examples', {})
        for db_type, examples in examples.items():
            manager = FewShotManager(db_type=db_type)
            manager.clear_examples()
            manager.add_examples(examples)


def get_similar_examples_for_query(query: str, db_type: str = "mysql", n_results: int = 3) -> List[Dict[str, str]]:
    """
    Get similar examples for a natural language query

    Args:
        query: Natural language query
        db_type: Database type ('mysql' or 'sqlserver')
        n_results: Number of examples to retrieve

    Returns:
        List of dictionaries with 'prompt' and 'sql' keys
    """
    manager = FewShotManager(db_type=db_type)
    return manager.get_similar_examples(query, n_results)


if __name__ == "__main__":
    # Example usage
    # First populate the database
    populate_examples()

    # Test retrieving examples
    test_queries = [
        "Show me my expenses from January",
        "What was my total spending on groceries?",
        "What are the online vs. offline sales?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        examples = get_similar_examples_for_query(query)
        for i, example in enumerate(examples):
            print(f"\nExample {i + 1}:")
            print(f"Prompt: {example['prompt']}")
            print(f"SQL: {example['sql']}")
