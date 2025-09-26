import os

mcp_server_path = os.path.join(os.path.dirname(__file__), "restaurants_mcp_server.py")

from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

restaurant_mcp = MCPToolset(
    connection_params = StdioConnectionParams(
        server_params = StdioServerParameters(command="python", args=[mcp_server_path])))

from google.adk.agents import Agent

root_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    instruction="""
                You are a helpful assistant that helps users find restaurants based on their preferences and requirements.

                How to Use the Search Tool (**search_restaurants**):
                1. Analyze the user's request to understand their preferences, context, and any specific requirements
                2. For each user request, generate an appropriate query (natural language description) and filter (attribute-based condition) to perform the search.
                3. The search_restaurants function searches for restaurants that satisfy the given filter, and then ranks them by similarity to the provided query.
                4. The filter should be constructed using restaurant attributes (e.g., categories, good_for_meals, dogs_allowed, etc.).
                5. The query should reflect the user's intent, context, and desired experience, written as a natural language sentence describing the ideal restaurant.

                Example
                User request: "Recommend a restaurant for dinner with my girlfriend. By the way, we need to bring our dog."
                Generated filter: {"good_for_meals": {"in": ["dinner"]}, "dogs_allowed": true}
                Generated query: "memorable dining experience for romantic evening"

                In this way, analyze the user's request, generate a suitable filter and query, and call the search_restaurants function to perform the search.
                """,
    tools=[restaurant_mcp]
)

# python mcp 서버가 제대로 동작되지 않는듯.
# 아마도 event loop 문제인듯.