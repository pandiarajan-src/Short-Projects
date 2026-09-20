"""
"""

import chromadb

CLIENT = chromadb.PersistentClient(path="./ChromaDB_Data")
COLLECTION = CLIENT.get_or_create_collection("notes")

# if COLLECTION.count() == 0:
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
