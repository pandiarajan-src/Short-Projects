"""
"""

import chromadb

CLIENT = chromadb.Client() # In-Memory on the RAM
COLLECTION = CLIENT.create_collection("smoke_test")

COLLECTION.add(
    ids=["a", "b", "c", "d"],
    documents=[
        "The espresso machine needs descaling every two months.",
        "Sharks are cartilaginous fish found in all oceans.",
        "Grind size is the biggest variable in espresso extraction.", 
        "Coffee add caffine to your blood that makes you awake and avoid sleep"       
    ],
)

print(f"Collection count: {COLLECTION.count()}")

if __name__ == "__main__":
    user_query = input("Give your Query to get data: => ")
    if len(user_query) > 0 or user_query is not None:
        RESULT = COLLECTION.query(query_texts=[user_query], n_results=2)
        for doc, dist in zip(RESULT["documents"][0], RESULT["distances"][0]):
            print(f"{dist:.4f} {doc}")


