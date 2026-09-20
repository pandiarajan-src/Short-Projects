"""
Make sure before running this script, you run chroma
```chroma run --host localhost --port 8000 --path ./chroma_server_data```
"""

import chromadb

CLIENT = chromadb.HttpClient(host="localhost", port="8000")

print(f"Detecing heartbeat: {CLIENT.heartbeat()}") # nanosecond time stamp

COLLECTION = CLIENT.get_or_create_collection("notes1")

print(f"Collection count : {COLLECTION.count()}")

COLLECTION.add(
    ids=["a1", "a2", "a3", "a4"], 
    documents=[
        "Chroma stores vectors on disk under ./chroma_data",
        "The espresso machine needs descaling every two months.",
        "Sharks are cartilaginous fish found in all oceans.",
        "Grind size is the biggest variable in espresso extraction.",            
    ]
)
print("seeded")

print(f"Collection count : {COLLECTION.count()}")

user_query = input("Enter your query: => ")
RESULT = COLLECTION.query(query_texts=[user_query], n_results=2)
for doc, dist in zip(RESULT["documents"][0], RESULT["distances"][0]):
    print(f"{dist:.4f}  {doc}")