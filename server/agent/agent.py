from google.adk.agents import Agent

from .search_agent import search_agent
from .reservation_agent import reservation_agent

root_agent = Agent(
    name="restaurant_agent",
    model="gemini-2.0-flash",
    instruction="""
                You are the manager of a service that helps with restaurant search/recommendation and reservations.
                Depending on the user's request, you should call the appropriate sub-agent to handle the task. **Do not handle the user's request directly**.
                For search or recommendation requests, use the **restaurant_search_agent** sub-agent.
                For reservation requests, use the **restaurant_reservation_agent** sub-agent.
                """,
    sub_agents=[search_agent, reservation_agent]
)
