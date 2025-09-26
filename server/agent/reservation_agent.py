
from datetime import datetime
def get_today():
    """
    Returns the current date in "YYYY-MM-DD DayOfWeek" format.
    """
    return datetime.now().strftime("%Y-%m-%d %A")

def reserve_restaurant(restaurant_id: str, datetime: str, people: int) -> dict:
    """
    Simulates a restaurant reservation.

    Args:
        restaurant_id (str): The ID of the restaurant to reserve.
        datetime (str): The reservation date and time in ISO 8601 format (e.g., "2023-10-15T19:30").
        people (int): The number of people for the reservation.

    Returns:
        dict: A dictionary containing the reservation details with the following keys:
            - "restaurant_id" (str): The ID of the reserved restaurant.
            - "datetime" (str): The reservation date and time in ISO 8601 format.
            - "people" (int): The number of people for the reservation.
            - "status" (str): The status of the reservation.
    """
    print(f"Reserving restaurant {restaurant_id} on {datetime} for {people} people.")

    return {
        "restaurant_id": restaurant_id,
        "datetime": datetime,
        "people": people,
        "status": "confirmed"
    }

from .restaurants import Reservation
from google.adk.agents import Agent

reservation_agent = Agent(
    name="restaurant_reservation_agent",
    model="gemini-2.0-flash",
    instruction="""
                # You are an assistant that helps with restaurant reservations. Select the restaurant to reserve, specify the reservation date/time and the number of people, and proceed with the reservation.
                    - The current reservation state is as follows:
                    {reservation}

                ## Instructions
                1. Check if the user has selected a restaurant to reserve. (**selected** field).
                    - The list of recommended restaurants is as follows:
                      {restaurants}
                    - Verify that the restaurant selected by the user is in this list, set the index of the selected restaurant in the **selected** field, and set the reservation status (**status**) field to "created".
                    - The index is 1-based. If the selected restaurant is the first in the list, set **selected** to 1.
                2. Check if the user has provided the reservation date/time (**datetime**) and the number of people (**people**).
                    - To check today's date, you can use the **get_today** tool.
                    - Set the **datetime** field with the reservation date/time provided by the user. The reservation date/time must be in ISO 8601 format (e.g., "2023-10-15T19:30").
                    - Set the **people** field with the number of people provided by the user.
                5. If the user confirms to reserve the selected restaurant, use the **reserve_restaurant** tool to make the reservation.
                6. If the reservation is successful, set the reservation status (**status**) to "confirmed".
                7. If the reservation is not completed, set the reservation status (**status**) to "pending".
                8. **Do not include any explanations or additional text in your response; only provide the final reservation details in the specified format.**
                """,
    output_schema=Reservation,
    output_key="reservation",
    tools=[get_today, reserve_restaurant],
)
