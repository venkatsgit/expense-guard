from expense_classifier import ExpenseClassifier
import pprint

# Initialize the enhanced classifier with your config file
classifier = ExpenseClassifier(
    "config.yaml",
    classification_model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",  # Free model with good performance
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # Free embedding model
)

# Sample transactions to classify
transactions = [
    "Grab Ride",
    "Mustafa Centre purchase",
    "Cathay Cinemas",
    "McDonald's Drive Thru",
    "SP Group March Bill",
    "Guardian Pharmacy Purchase",
    "Cold Storage Weekly Shopping",
    "Netflix Monthly Subscription",
    "Uniqlo Shirt Purchase",
    "Spring Airlines Ticket"
]

# Classify the transactions
categories = classifier.classify(transactions)

# Print the results
print("Classification Results:")
print("-" * 50)
for transaction, category in zip(transactions, categories):
    print(f"{transaction:<30} → {category}")

# Let's look at the confidence scores for a specific transaction
print("\nDetailed analysis for 'Mustafa Centre purchase':")
print("-" * 50)
confidence_scores = classifier.get_confidence_scores("Mustafa Centre purchase")
pprint.pprint(confidence_scores)

# Add some new examples and see if it improves classification
print("\nAdding new examples and reclassifying...")
new_examples = [
    {"transaction": "NTUC Shopping", "category": "Groceries"},
    {"transaction": "Giant Supermarket", "category": "Groceries"},
    {"transaction": "Grab to Office", "category": "Transport"},
    {"transaction": "Shaw Theatres", "category": "Entertainment"}
]
classifier.add_examples(new_examples)

# Reclassify with new examples
new_categories = classifier.classify(transactions)

# Print the new results
print("\nUpdated Classification Results:")
print("-" * 50)
for transaction, old_cat, new_cat in zip(transactions, categories, new_categories):
    changed = "✓" if old_cat != new_cat else " "
    print(f"{transaction:<30} → {new_cat} {changed}")