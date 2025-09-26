import os
import json

input_json_file_path = os.path.join(os.path.dirname(__file__), "restaurant_desc.json")
with open(input_json_file_path, 'r', encoding='utf-8') as file:
    restaurants = json.load(file)

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

for count, restaurant in enumerate(restaurants, start=1):
    print(f"Processing restaurant {count}: {restaurant["id"]}")
    restaurant["vector"] = model.encode(restaurant["description"]).tolist()

for restaurant in restaurants:
    restaurant.pop("description", None)

output_json_file_path = os.path.join(os.path.dirname(__file__), "restaurant_vector.json")
with open(output_json_file_path, 'w', encoding='utf-8') as outfile:
    json.dump(restaurants, outfile, ensure_ascii=False, indent=2)
