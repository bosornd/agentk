import asyncio
from fastmcp import Client

import os

mcp_server_path = os.path.join(os.path.dirname(__file__), "restaurants_mcp_server.py")
client = Client(mcp_server_path)

async def main():
    async with client:
        # Basic server interaction
        await client.ping()
        
        tools = await client.list_tools()
        for tool in tools:
            print(f"Tool: {tool.name}, Description: {tool.description}")
        
        # Execute operations
        result = await client.call_tool("search_restaurants", {"query": "memorable dining experience for romantic evening", "filter": {"good_for_meals": {"in": ["dinner"]}, "dogs_allowed": True}, "top_k": 5})
        restaurants = result.structured_content.get("result", []) if result.structured_content else []

        for idx, restaurant in enumerate(restaurants, start=1):
            print(f"{idx}. {restaurant['name']} - {restaurant['good_for_meals']} - Rating: {restaurant['dogs_allowed']}")

if __name__ == "__main__":
    asyncio.run(main())