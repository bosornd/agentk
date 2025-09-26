# Pydantic models for restaurant data
from pydantic import BaseModel, Field
from typing import Any, List

class Location(BaseModel):
    lon: float = Field(..., description="Longitude of the restaurant's location.")
    lat: float = Field(..., description="Latitude of the restaurant's location.")

class Restaurant(BaseModel):
    id: str = Field(..., description="Unique identifier for the restaurant.")
    name: str = Field(..., description="Name of the restaurant.")
    address: str = Field(..., description="Street address of the restaurant.")
#    city: str = Field(..., description="City where the restaurant is located.")
#    state: str = Field(..., description="State where the restaurant is located.")
#    postal_code: str = Field(..., description="Postal (ZIP) code of the restaurant's location.")
    stars: float = Field(..., description="Star rating of the restaurant (integer value).")
    review_count: int = Field(..., description="Number of reviews for the restaurant.")
#    categories: List[str] = Field(default_factory=list, description="List of categories or cuisines the restaurant belongs to.")
#    location: Location = Field(..., description="Geographical location (longitude and latitude) of the restaurant.")
#    ambiences: List[str] = Field(default_factory=list, description="List of ambience types (e.g., hipster, trendy, casual).")
#    good_for_kids: bool = Field(default=False, description="Whether the restaurant is suitable for kids.")
#    has_tv: bool = Field(default=False, description="Whether the restaurant has a TV available.")
#    good_for_meals: List[str] = Field(default_factory=list, description="List of meal types the restaurant is good for (e.g., lunch, brunch, breakfast).")
#    dogs_allowed: bool = Field(default=False, description="Whether dogs are allowed at the restaurant.")
#    happy_hour: bool = Field(default=False, description="Whether the restaurant offers a happy hour.")
#    parkings: List[str] = Field(default_factory=list, description="List of available parking options (e.g., street, lot).")
#    wifi: bool = Field(default=False, description="Whether the restaurant provides WiFi access.")
    description: str = Field(..., description="General description of the restaurant.")

class RestaurantList(BaseModel):
    restaurants: List[Restaurant] = Field(..., description="List of searched/recommended restaurants.")

class Reservation(BaseModel):
    selected: int = Field(default=0, description="Identifier of the selected restaurant from the search results.")
    people: int = Field(default=0, description="Number of people for the reservation.")
    datetime: str = Field(default="", description="Time of the reservation in ISO 8601 format.")
    status: str = Field(default="created", description="Status of the reservation.")


from sentence_transformers import SentenceTransformer
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

from qdrant_client import QdrantClient
client = QdrantClient()

from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

def _parse_filter(filters: dict):
    must_conditions = []
    must_not_conditions = []
    should_conditions = []

    for key, cond in filters.items():
        if not isinstance(cond, dict):
            must_conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=cond)
                )
            )
            continue

        for op, value in cond.items():
            if op == "eq":
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            elif op == "ne":
                must_not_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            elif op == "gt":
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        range=Range(gt=value)
                    )
                )
            elif op == "lt":
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        range=Range(lt=value)
                    )
                )
            elif op == "gte":
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        range=Range(gte=value)
                    )
                )
            elif op == "lte":
                must_conditions.append(
                    FieldCondition(
                        key=key,
                        range=Range(lte=value)
                    )
                )
            elif op == "in":
                for v in value:
                    should_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=v)
                        )
                    )

    return Filter(
        must=must_conditions if must_conditions else None,
        must_not=must_not_conditions if must_not_conditions else None,
        should=should_conditions if should_conditions else None,
    )

def search_restaurants(query: str, filter: dict, top_k: int) -> list[dict]:
    """
    Searches for restaurants using a combination of semantic similarity search on a query description and optional filtering conditions.
    
    The function performs a vector similarity search based on the provided query string, which should describe desired restaurant attributes (e.g., "good food and service"). It uses a pre-trained embedding model to encode the query and find the most similar restaurants in the vector database. Additionally, filters can be applied to narrow down results based on specific field values.
    
    Args:
        query (str): A natural language description of the desired restaurant (e.g., "restaurants with good food and service"). This is used for semantic similarity search against stored restaurant descriptions.
        filter (dict): A dictionary specifying filtering conditions on restaurant fields. Supports the following formats:
            - Simple equality: {"field_name": value} – matches restaurants where 'field_name' equals 'value' (equivalent to {"field_name": {"eq": value}}).
            - Operator-based conditions: {"field_name": {"op": value}} where 'op' can be:
                - "eq": equals value.
                - "ne": not equals value.
                - "gt": greater than value (for numeric fields).
                - "gte": greater than or equal to value (for numeric fields).
                - "lt": less than value (for numeric fields).
                - "lte": less than or equal to value (for numeric fields).
            - For array fields like 'categories' (list of strings), additional operators are supported:
                - {"categories": {"in": ["value1", "value2"]}} – matches if the array contains any of the specified values.
            Multiple conditions can be combined in the filter dict (e.g., {"stars": {"gte": 4.0}, "categories": {"in": ["Italian", "Pizza"]}}).
            Supported fields and their types:
                - String fields: id, name, address, city, state, postal_code.
                - Numeric fields: stars (float), review_count (int).
                - Boolean fields: good_for_kids, has_tv, dogs_allowed, happy_hour, wifi.
                - Array fields (lists of strings):
                    - categories: Possible values include Acai Bowls, American (New), American (Traditional), Argentine, Asian Fusion, Australian, Bagels, Bakeries, Barbeque, Bars, Basque, Beer, Beer Bar, Beer Gardens, Belgian, Brazilian, Breakfast & Brunch, Breweries, Brewpubs, British, Bubble Tea, Buffets, Burgers, Butcher, Cafes, Cafeteria, Cajun/Creole, Cantonese, Caribbean, Caterers, Champagne Bars, Cheese Shops, Chicken Shop, Chicken Wings, Chinese, Cocktail Bars, Coffee & Tea, Coffee Roasteries, Coffeeshops, Comfort Food, Creperies, Cuban, Cupcakes, Delicatessen, Delis, Desserts, Dim Sum, Diners, Dive Bars, Do-It-Yourself Food, Donuts, Empanadas, Ethiopian, Ethnic Food, Ethnic Grocery, Falafel, Farmers Market, Fast Food, Fish & Chips, Fondue, Food Court, Food Delivery Services, Food Stands, Food Tours, Food Trucks, French, Fruits & Veggies, Gastropubs, Gelato, German, Gluten-Free, Greek, Grocery, Halal, Hawaiian, Health Markets, Himalayan/Nepalese, Hookah Bars, Hot Dogs, Hot Pot, Hotels, Ice Cream & Frozen Yogurt, Imported Food, Indian, Indonesian, International Grocery, Irish, Italian, Japanese, Juice Bars & Smoothies, Kebab, Korean, Latin American, Lebanese, Live/Raw Food, Local Flavor, Lounges, Meat Shops, Mediterranean, Mexican, Middle Eastern, Modern European, Moroccan, New Mexican Cuisine, Noodles, Organic Stores, Pakistani, Pasta Shops, Patisserie/Cake Shop, Personal Chefs, Peruvian, Piano Bars, Pizza, Poke, Pop-Up Restaurants, Public Markets, Pubs, Ramen, Salad, Sandwiches, Scandinavian, Seafood, Seafood Markets, Soul Food, Soup, Southern, Spanish, Speakeasies, Specialty Food, Sports Bars, Steakhouses, Street Vendors, Sushi Bars, Szechuan, Tacos, Tapas Bars, Tapas/Small Plates, Tasting Classes, Tex-Mex, Thai, Themed Cafes, Turkish, Tuscan, Vegan, Vegetarian, Vietnamese, Whiskey Bars, Wine & Spirits, Wine Bars, Wine Tasting Classes, Wine Tasting Room, Wine Tours, Wineries, Wraps.
                    - ambiences: Possible values include casual, classy, divey, hipster, intimate, romantic, touristy, trendy, upscale.
                    - good_for_meals: Possible values include breakfast, brunch, dessert, dinner, latenight, lunch.
                    - parkings: Possible values include garage, lot, street, valet, validated.
                - Location field: location (dict with 'lon' and 'lat' as floats).
        top_k (int, optional): The number of top similar restaurants to return.
    
    Returns:
        list[dict]: A list of restaurant dictionaries matching the query and filters, each containing fields like id, name, stars, etc. Results are ranked by similarity to the query.
    
    Example:
        # Search for restaurants with good food and service, rated 4+ stars, in Italian or Pizza categories
        results = search_restaurants(
            query="restaurants with delicious food and excellent service",
            filter={"stars": {"gte": 4.0}, "categories": {"in": ["Italian", "Pizza"]}},
            top_k=5
        )
        for restaurant in results:
            print(f"{restaurant['name']} - {restaurant['stars']} stars")
    """
    near_points = client.query_points(
        collection_name="restaurants",
        query=model.encode(query).tolist(),
        query_filter=_parse_filter(filter),
        limit=top_k
    )

    fields = ["id", "name", "address", "stars", "review_count", "description"]
    return [
        {k: point.payload.get(k) for k in fields if point.payload and k in point.payload}
        for point in near_points.points if point.payload is not None
    ]

"""
    id: str = Field(..., description="Unique identifier for the restaurant.")
    name: str = Field(..., description="Name of the restaurant.")
    address: str = Field(..., description="Street address of the restaurant.")
#    city: str = Field(..., description="City where the restaurant is located.")
#    state: str = Field(..., description="State where the restaurant is located.")
#    postal_code: str = Field(..., description="Postal (ZIP) code of the restaurant's location.")
    stars: float = Field(..., description="Star rating of the restaurant (integer value).")
    review_count: int = Field(..., description="Number of reviews for the restaurant.")
#    categories: List[str] = Field(default_factory=list, description="List of categories or cuisines the restaurant belongs to.")
#    location: Location = Field(..., description="Geographical location (longitude and latitude) of the restaurant.")
#    ambiences: List[str] = Field(default_factory=list, description="List of ambience types (e.g., hipster, trendy, casual).")
#    good_for_kids: bool = Field(default=False, description="Whether the restaurant is suitable for kids.")
#    has_tv: bool = Field(default=False, description="Whether the restaurant has a TV available.")
#    good_for_meals: List[str] = Field(default_factory=list, description="List of meal types the restaurant is good for (e.g., lunch, brunch, breakfast).")
#    dogs_allowed: bool = Field(default=False, description="Whether dogs are allowed at the restaurant.")
#    happy_hour: bool = Field(default=False, description="Whether the restaurant offers a happy hour.")
#    parkings: List[str] = Field(default_factory=list, description="List of available parking options (e.g., street, lot).")
#    wifi: bool = Field(default=False, description="Whether the restaurant provides WiFi access.")
    description: str = Field(..., description="General description of the restaurant.")

"""
