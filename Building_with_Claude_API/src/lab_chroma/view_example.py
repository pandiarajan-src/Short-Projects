"""
"""

import chromadb
import pandas as pd

CLIENT = chromadb.Client() # In-Memory on the RAM
COLLECTION = CLIENT.create_collection("view_example")

COLLECTION.add(
    ids=["a", "b", "c", "d", "e"],
    documents=[
        "The espresso machine needs descaling every two months.",
        "Sharks are cartilaginous fish found in all oceans.",
        "Grind size is the biggest variable in espresso extraction.", 
        "Coffee add caffine to your blood that makes you awake and avoid sleep",
        "I am a human, how I am doing depends on how I think"       
    ],
)

print(f"Collection count: {COLLECTION.count()}")
print(f"Peek of 2 records: {COLLECTION.peek(limit=2)}")
print(f"Paged Browse of 2 records: {COLLECTION.get(limit=2, include=["documents", "metadatas"])}")
print(f"Get specified record: {COLLECTION.get(ids=["a"], include=["documents", "embeddings"])}")

## Convert data to panda data frame
RECORD = COLLECTION.get(ids=["a", "b", "c"], include=["documents", "embeddings"])
DF = pd.DataFrame({"id": RECORD["ids"], "doc": RECORD["documents"], **{"meta": RECORD["metadatas"]}})
print(DF.head(10).to_string())




