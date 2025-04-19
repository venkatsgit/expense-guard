import json
import os
from typing import List, Dict, Any, Optional
import yaml
import numpy as np
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util


class ExpenseClassifier:
    def __init__(self, config_path: str,
                 classification_model: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the enhanced expense classifier with configuration from a file.

        Args:
            config_path: Path to the configuration file (YAML or JSON)
            classification_model: Name of the Hugging Face model for zero-shot classification
            embedding_model: Name of the Hugging Face model for embeddings (few-shot learning)
        """
        self.config = self._load_config(config_path)
        self.categories = self.config.get("categories", [])
        self.rules = self.config.get("rules", {})
        self.examples = self.config.get("examples", [])

        # Initialize the classification pipeline
        self.classifier = pipeline(
            "zero-shot-classification",
            model=classification_model,
            device=-1  # Use CPU; set to GPU index if available
        )

        # Initialize the sentence transformer for few-shot learning
        self.sentence_model = SentenceTransformer(embedding_model)

        # Pre-compute embeddings for examples
        self._prepare_example_embeddings()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as file:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(file)
            elif config_path.endswith('.json'):
                return json.load(file)
            else:
                raise ValueError("Config file must be YAML or JSON")

    def _prepare_example_embeddings(self):
        """Pre-compute embeddings for all examples for faster few-shot learning."""
        if not self.examples:
            self.example_embeddings = []
            self.example_categories = []
            return

        # Extract text and categories from examples
        example_texts = [example['transaction'] for example in self.examples]
        self.example_categories = [example['category'] for example in self.examples]

        # Calculate embeddings
        self.example_embeddings = self.sentence_model.encode(example_texts)

    def _prepare_hypotheses(self) -> List[str]:
        """
        Prepare hypotheses for zero-shot classification based on rules.

        Returns:
            A list of formatted hypotheses for the classifier
        """
        hypotheses = []

        # Create a hypothesis for each category
        for category in self.categories:
            # Start with the basic category
            hypothesis = f"This is a {category} expense"

            # Add rule information if available
            rule_key = category.lower()
            if rule_key in self.rules:
                hypothesis += f" ({self.rules[rule_key]})"

            hypotheses.append(hypothesis)
        print("hypothseses",hypotheses )
        return hypotheses

    def _few_shot_classify(self, transaction: str, k: int = 5) -> Dict[str, float]:
        """
        Classify a transaction using few-shot learning by comparing to examples.

        Args:
            transaction: Transaction text to classify
            k: Number of nearest neighbors to consider

        Returns:
            Dictionary mapping categories to confidence scores
        """
        if not self.example_embeddings.any():
            return {}

        # Get embedding for the transaction
        transaction_embedding = self.sentence_model.encode(transaction)

        # Calculate cosine similarities
        similarities = util.cos_sim(transaction_embedding, self.example_embeddings)[0]

        # Get top-k most similar examples
        if k > len(similarities):
            k = len(similarities)

        top_k_indices = np.argsort(similarities)[-k:]

        # Count categories of most similar examples
        category_scores = {}
        for idx in top_k_indices:
            category = self.example_categories[idx]
            similarity = similarities[idx].item()

            # Weight by similarity
            if category not in category_scores:
                category_scores[category] = 0
            category_scores[category] += similarity

        # Normalize scores
        total = sum(category_scores.values())
        if total > 0:
            for category in category_scores:
                category_scores[category] /= total

        return category_scores

    def classify(self, transactions: List[str], batch_size: int = 16) -> List[str]:
        """
        Classify a list of transaction descriptions into predefined categories.
        Uses a hybrid approach combining zero-shot and few-shot classification.

        Args:
            transactions: List of transaction descriptions
            batch_size: Number of transactions to process in one batch

        Returns:
            List of assigned categories in the same order as input transactions
        """
        results = []
        hypotheses = self._prepare_hypotheses()

        # Process in batches
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]

            # Run zero-shot classification
            batch_results = self.classifier(
                batch,
                hypotheses,
                multi_label=False
            )
            print("batch_results",batch_results)
            # Combine with few-shot results
            categories = []
            for j, result in enumerate(batch_results):
                transaction = batch[j]

                # Get zero-shot scores
                zero_shot_scores = {}
                for idx, label in enumerate(result['labels']):
                    category_idx = hypotheses.index(label)
                    category = self.categories[category_idx]
                    zero_shot_scores[category] = result['scores'][idx]

                # Get few-shot scores
                few_shot_scores = self._few_shot_classify(transaction)

                # Combine scores (simple weighted average)
                combined_scores = {}
                for category in self.categories:
                    zero_score = zero_shot_scores.get(category, 0.0)
                    few_score = few_shot_scores.get(category, 0.0)

                    # Give more weight to few-shot if we have examples
                    weight = 0.7 if few_shot_scores else 0.0
                    combined_scores[category] = (1 - weight) * zero_score + weight * few_score

                # Get top category
                if combined_scores:
                    top_category = max(combined_scores.items(), key=lambda x: x[1])[0]
                    categories.append(top_category)
                else:
                    # Fallback to zero-shot top result
                    top_idx = result['scores'].index(max(result['scores']))
                    category_name = self.categories[top_idx]
                    categories.append(category_name)

            results.extend(categories)

        return results

    def add_examples(self, new_examples: List[Dict[str, str]]) -> None:
        """
        Add new example transactions to the classifier and update embeddings.

        Args:
            new_examples: List of dictionaries with 'transaction' and 'category' keys
        """
        added = False
        for example in new_examples:
            if 'transaction' in example and 'category' in example:
                if example['category'] in self.categories:
                    self.examples.append(example)
                    added = True

        # Recompute embeddings if we added examples
        if added:
            self._prepare_example_embeddings()

    def add_rule(self, category: str, rule_description: str) -> None:
        """
        Add or update a rule for a category.

        Args:
            category: The category name (case-sensitive)
            rule_description: The rule description text
        """
        if category in self.categories:
            self.rules[category.lower()] = rule_description

    def get_confidence_scores(self, transaction: str) -> Dict[str, float]:
        """
        Get confidence scores for all categories for a single transaction.

        Args:
            transaction: Transaction text to classify

        Returns:
            Dictionary mapping category names to confidence scores
        """
        hypotheses = self._prepare_hypotheses()

        # Run zero-shot classification
        result = self.classifier(transaction, hypotheses, multi_label=False)

        # Get zero-shot scores
        zero_shot_scores = {}
        for idx, label in enumerate(result['labels']):
            category_idx = hypotheses.index(label)
            category = self.categories[category_idx]
            zero_shot_scores[category] = result['scores'][idx]

        # Get few-shot scores
        few_shot_scores = self._few_shot_classify(transaction)

        # Combine scores (simple weighted average)
        combined_scores = {}
        for category in self.categories:
            zero_score = zero_shot_scores.get(category, 0.0)
            few_score = few_shot_scores.get(category, 0.0)

            # Give more weight to few-shot if we have examples
            weight = 0.7 if few_shot_scores else 0.0
            combined_scores[category] = (1 - weight) * zero_score + weight * few_score

        return combined_scores