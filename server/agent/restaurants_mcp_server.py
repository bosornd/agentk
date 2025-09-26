from .restaurants import search_restaurants as _search_restaurants

# pip install fastmcp
from fastmcp import FastMCP

mcp = FastMCP("restaurant_search")

@mcp.tool()
def search_restaurants(query: str, filter: dict = {}, top_k: int = 5) -> list[dict]:
    f"""
    {_search_restaurants.__doc__}
    """

    return _search_restaurants(query, filter, top_k)

if __name__ == "__main__":
    mcp.run()
