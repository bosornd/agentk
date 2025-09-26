import os
import json

restaurant_json_file_path = os.path.join(os.path.dirname(__file__), "restaurant.json")
with open(restaurant_json_file_path, 'r', encoding='utf-8') as file:
    restaurants = json.load(file)

desc_json_file_path = os.path.join(os.path.dirname(__file__), "restaurant_desc.json")
with open(desc_json_file_path, 'r', encoding='utf-8') as file:
    restaurant_desc = json.load(file)

vector_json_file_path = os.path.join(os.path.dirname(__file__), "restaurant_vector.json")
with open(vector_json_file_path, 'r', encoding='utf-8') as file:
    restaurant_vector = json.load(file)

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
embedding_dim = model.get_sentence_embedding_dimension()
if embedding_dim is None:
    raise ValueError("The model did not return a valid embedding dimension.")

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

points = []
for count, restaurant in enumerate(restaurants, start=1):
    restaurant_id = restaurant.get('id', restaurant.get('business_id'))
    desc_entry = next((item for item in restaurant_desc if item['id'] == restaurant_id), None)
    vector_entry = next((item for item in restaurant_vector if item['id'] == restaurant_id), None)

    restaurant["description"] = desc_entry.get("description") if desc_entry else None
    
    if vector_entry:
        point = PointStruct(
            id=count,
            vector=vector_entry["vector"],
            payload=restaurant
        )
        points.append(point)


client = QdrantClient() # Connect to Qdrant (default: localhost:6333)

collection_name = "restaurants"

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
)

client.upsert(collection_name=collection_name, points=points)
