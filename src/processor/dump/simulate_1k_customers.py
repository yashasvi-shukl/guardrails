import random
import json
from pymongo import MongoClient

# List of possible guardrail IDs
input_guardrails_list = range(30000, 30008)
output_guardrails_list = range(20000, 20018)

def generate_document(customer_id):
    # Generate a random 5-digit customer ID
    # customer_id = random.randint(10000, 99999)
    
    # Randomly pick 3 unique IDs from each guardrail list
    sequential_ids = [20000, 30000] +random.sample(input_guardrails_list, 3)
    parallel_ids = random.sample(output_guardrails_list, 5)
    
    # Ensure no duplicates in each list
    sequential_ids = list(set(sequential_ids))
    parallel_ids = list(set(parallel_ids))
    
    # Create the document
    document = {
        "customer_id": customer_id,
        "rag_policy": {
            "semantic_search": {},
            "prompt": {}
        },
        "guardrail_policy": {
            "sequential": sequential_ids,
            "parallel": parallel_ids
        }
    }
    
    return document

# Generate 1000 documents
documents = [generate_document(customer_id=customer_id) for customer_id in range(10000, 11000)]

# Insert the documents into the collection
try:
    client = MongoClient("mongodb+srv://kritaka_user:q3DCrlV5gg2xZZYr@cluster0.jkkz8m5.mongodb.net/admin?appName=Cluster0")
    db = client["kritaka_admin"]
    collection = db["customer_policies"]
    collection.insert_many(documents)
    print("Generated 1000 simulated documents.")
except Exception as e:
    print(f"Error: {e}")