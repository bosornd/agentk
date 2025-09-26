import os
import json
from collections import Counter

json_file_path = os.path.join(os.path.dirname(__file__), "restaurant.json")
with open(json_file_path, 'r', encoding='utf-8') as file:
    restaurants = json.load(file)

def get_unique_values(field_name):
    """Get unique values from a specific field across all restaurants"""
    all_values = []
    for restaurant in restaurants:
        field_data = restaurant.get(field_name, [])
        if isinstance(field_data, list):
            all_values.extend(field_data)
        elif field_data:  # Handle non-list values
            all_values.append(field_data)
    
    return sorted(list(set(all_values)))

def get_value_counts(field_name):
    """Get count of each value in a specific field"""
    all_values = []
    for restaurant in restaurants:
        field_data = restaurant.get(field_name, [])
        if isinstance(field_data, list):
            all_values.extend(field_data)
        elif field_data:
            all_values.append(field_data)
    
    return Counter(all_values)

def analyze_restaurant_fields():
    """Analyze and print unique values for categories, ambiences, good_for_meals, and parkings"""
    fields_to_analyze = ['categories', 'ambiences', 'good_for_meals', 'parkings']
    
    print(f"Total restaurants: {len(restaurants)}\n")
    
    for field in fields_to_analyze:
        print(f"=== {field.upper()} ===")
        unique_values = get_unique_values(field)
        value_counts = get_value_counts(field)
        
        print(f"Total unique {field}: {len(unique_values)}")
        
        # Print all values in one line
        print(f"{field}: {', '.join(unique_values)}")
        
        print("Values with counts:")
        
        # Sort by count (descending) then by name
        sorted_counts = sorted(value_counts.items(), key=lambda x: (-x[1], x[0]))
        
        for value, count in sorted_counts:
            print(f"  {value}: {count}")
        
        print()  # Empty line for spacing

if __name__ == "__main__":
    analyze_restaurant_fields()

# categories: Acai Bowls, American (New), American (Traditional), Argentine, Asian Fusion, Australian, Bagels, Bakeries, Barbeque, Bars, Basque, Beer, Beer Bar, Beer Gardens, Belgian, Brazilian, Breakfast & Brunch, Breweries, Brewpubs, British, Bubble Tea, Buffets, Burgers, Butcher, Cafes, Cafeteria, Cajun/Creole, Cantonese, Caribbean, Caterers, Champagne Bars, Cheese Shops, Chicken Shop, Chicken Wings, Chinese, Cocktail Bars, Coffee & Tea, Coffee Roasteries, Coffeeshops, Comfort Food, Creperies, Cuban, Cupcakes, Delicatessen, Delis, Desserts, Dim Sum, Diners, Dive Bars, Do-It-Yourself Food, Donuts, Empanadas, Ethiopian, Ethnic Food, Ethnic Grocery, Falafel, Farmers Market, Fast Food, Fish & Chips, Fondue, Food Court, Food Delivery Services, Food Stands, Food Tours, Food Trucks, French, Fruits & Veggies, Gastropubs, Gelato, German, Gluten-Free, Greek, Grocery, Halal, Hawaiian, Health Markets, Himalayan/Nepalese, Hookah Bars, Hot Dogs, Hot Pot, Hotels, Ice Cream & Frozen Yogurt, Imported Food, Indian, Indonesian, International Grocery, Irish, Italian, Japanese, Juice Bars & Smoothies, Kebab, Korean, Latin American, Lebanese, Live/Raw Food, Local Flavor, Lounges, Meat Shops, Mediterranean, Mexican, Middle Eastern, Modern European, Moroccan, New Mexican Cuisine, Noodles, Organic Stores, Pakistani, Pasta Shops, Patisserie/Cake Shop, Personal Chefs, Peruvian, Piano Bars, Pizza, Poke, Pop-Up Restaurants, Public Markets, Pubs, Ramen, Salad, Sandwiches, Scandinavian, Seafood, Seafood Markets, Soul Food, Soup, Southern, Spanish, Speakeasies, Specialty Food, Sports Bars, Steakhouses, Street Vendors, Sushi Bars, Szechuan, Tacos, Tapas Bars, Tapas/Small Plates, Tasting Classes, Tex-Mex, Thai, Themed Cafes, Turkish, Tuscan, Vegan, Vegetarian, Vietnamese, Whiskey Bars, Wine & Spirits, Wine Bars, Wine Tasting Classes, Wine Tasting Room, Wine Tours, Wineries, Wraps
# ambiences: casual, classy, divey, hipster, intimate, romantic, touristy, trendy, upscale
# good_for_meals: breakfast, brunch, dessert, dinner, latenight, lunch
# parkings: garage, lot, street, valet, validated