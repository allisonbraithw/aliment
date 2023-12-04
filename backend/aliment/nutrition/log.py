from pydantic import BaseModel
from pydantic.json import pydantic_encoder
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime
import json

from aliment.nutrition.plan import NutritionPlanModel
from aliment.dependency_factory import dependency_factory as df

load_dotenv()
client = df.openai_client


class Estimate(BaseModel):
    nutrient: str
    estimate: int
    units: str
    confidence: Optional[float] = None


class LogEntry(BaseModel):
    """A log entry for a meal."""
    meal_id: str
    datetime: str
    calories: Estimate
    protein_g: Estimate
    fat_g: Estimate
    carbs_g: Estimate
    micronutrients: Optional[List[Estimate]] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None

# todo(arb) I feel like I can extend this from LogEntry? can clean up?


class DailyLog:
    """A daily log of meals."""
    date: str
    entries: List[LogEntry]
    calories: str
    protein_g: str
    fat_g: str
    carbs_g: str
    # micronutrients: List[Estimate]

    def __init__(self, date: str, entries: List[LogEntry]):
        self.date = date
        self.entries = entries
        # sum the calories of each entry
        self.calories = f"{sum([e.calories.estimate for e in entries])} {
            entries[0].calories.units}"
        self.protein_g = f"{sum([e.protein_g.estimate for e in entries])} {
            entries[0].protein_g.units}"
        self.fat_g = f"{sum([e.fat_g.estimate for e in entries])} {
            entries[0].fat_g.units}"
        self.carbs_g = f"{sum([e.carbs_g.estimate for e in entries])} {
            entries[0].carbs_g.units}"
        # self.micronutrients = self._calculate_micronutrients()

    def generate_aggregated_log(self):
        """Generate an aggregated log of the daily log."""
        # todo(arb) implement

    def __str__(self):
        return f"""
        Date: {self.date}
        Entries: {self.entries}
        Calories: {self.calories}
        Protein: {self.protein_g}
        Fat: {self.fat_g}
        Carbs: {self.carbs_g}
        """


# region Prompts
def generate_base_system_prompt(user_plan: NutritionPlanModel, aggregated_daily_log: DailyLog):
    prompt = f"""
    You are a helpful nutritionist and meal planner. Users will chat with you to ask questions about what they should eat or if they should eat\
    specific things, based on their specified plan. You will be given a user's nutrition plan, and their questions. You have several functions \
    available to you to log the data when appropriate. The user's plan is as follows:
    {user_plan}

    So far today they have logged the following:
    {aggregated_daily_log}
    """
    return prompt


log_entry_system_prompt = f"""
    You are a helpful nutrition analysis. You will be given a meal description and asked to estimate the calories, protein, fat, and carbs in the meal.\
    You will also be asked to estimate the amount of specified micronutrients in the meal. For each estimate, provide a number, units, and a confidence score from 0 to 1.\
    The confidence score should be a decimal number between 0 and 1. 0 means you are not confident at all in your estimate, and 1 means you are very confident in your estimate.\
    The units should be a string, such as "grams" or "milligrams".\
    Return the estimates as a JSON object with the following format:
    {{
        "calories": {{
            "estimate": 100,
            "units": "grams",
            "confidence": 0.5
        }},
        "protein_g": {{
            "estimate": 100,
            "units": "grams",
            "confidence": 0.5
        }},
        "fat_g": {{
            "estimate": 100,
            "units": "grams",
            "confidence": 0.5
        }},
        "carbs_g": {{
            "estimate": 100,
            "units": "grams",
            "confidence": 0.5
        }},
        "micronutrients": [
            {{
                "nutrient": "vitamin a",
                "estimate": 100,
                "units": "mcg",
                "confidence": 0.5
            }},
            {{
                "nutrient": "vitamin b12",
                "estimate": 0.2,
                "units": "mcg",
                "confidence": 0.5
            }}
        ]
    }}
    """
# endregion


def handle_user_input(user_input: str) -> str:
    # Instructions to the agent to classify the user input as:
    # 1. Should I eat this? -> compare against the users plan and give feedback
    # 2. I just ate this -> create a log entry, update the users plan, and give feedback
    # 3. What should I eat -> check gaps in the user's plan and suggest foods to fill those gaps
    # get all entries from DB
    # aggregate entries by day
    example_daily_log = DailyLog(
        date=datetime.now().strftime("%Y-%m-%d"),
        entries=[
            LogEntry(
                meal_id="breakfast",
                datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                calories=Estimate(
                    nutrient="calories",
                    estimate=100,
                    units="grams",
                    confidence=0.5,
                ),
                protein_g=Estimate(
                    nutrient="protein",
                    estimate=50,
                    units="grams",
                    confidence=0.5,
                ),
                fat_g=Estimate(
                    nutrient="fat",
                    estimate=100,
                    units="grams",
                    confidence=0.5,
                ),
                carbs_g=Estimate(
                    nutrient="carbs",
                    estimate=100,
                    units="grams",
                    confidence=0.5,
                ),
            )
        ]
    )
    print(generate_base_system_prompt(get_user_daily_plan(
        user_id="test", date=datetime.now()), example_daily_log))
    messages = [
        {"role": "system", "content": generate_base_system_prompt(
            get_user_daily_plan(user_id="test", date=datetime.now()), example_daily_log)},
        {"role": "user", "content": user_input}
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_log_entry",
                "description": "Based on the description of a meal that has been eaten, generate nutrition estimates for that meal and save to the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meal_id": {
                            "type": "string",
                            "description": "Plaintext 2-3 word description of the meal based on time of day and what was eaten",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Notes about the meal, such as what was eaten, where it was eaten, and who it was eaten with",
                        }
                    },
                    "required": ["meal_id", "notes"],
                }
            }
        },
    ]
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        available_functions = {"generate_log_entry": generate_log_entry}
        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                **function_args
            )
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response, indent=4, default=pydantic_encoder),
            }
            )
        second_response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
        )
        print(second_response.choices[0].message.content)
        return second_response.choices[0].message.content
    else:
        print(response_message.content)
        return response_message.content


def get_user_daily_plan(user_id: str, date: datetime) -> NutritionPlanModel:
    # todo(arb) get plan from the db
    return NutritionPlanModel(
        start_date=date.strftime("%Y-%m-%d"),
        end_date=date.strftime("%Y-%m-%d"),
        status="active",
        calories=100,
        protein_g=100,
        fat_g=100,
        carbs_g=30,
        micronutrient_goals=[
            {
                "nutrient": "vitamin a",
                "goal": 900,
                "units": "mcg",
            },
            {
                "nutrient": "vitamin b12",
                "goal": 3,
                "units": "mcg",
            }
        ]
    )


def generate_log_entry(meal_id: str, notes: str = None, image_url: str = None) -> LogEntry:
    """Generate a log entry for a meal."""
    print("generate_log_entry function called")
    if notes is None and image_url is None:
        raise ValueError("Must provide either notes or image_url.")

    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": log_entry_system_prompt,
            },
            {
                "role": "user",
                "content": notes
            }
        ]
    )
    print(response.choices[0].message.content)
    response_content_json = json.loads(response.choices[0].message.content)
    # todo(arb) write to DB
    return LogEntry(
        meal_id=meal_id,
        datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        calories=Estimate(
            nutrient="calories",
            estimate=response_content_json.get("calories").get("estimate"),
            units=response_content_json["calories"]["units"],
            confidence=response_content_json["calories"]["confidence"],
        ),
        protein_g=Estimate(
            nutrient="protein",
            estimate=response_content_json["protein_g"]["estimate"],
            units=response_content_json["protein_g"]["units"],
            confidence=response_content_json["protein_g"]["confidence"],
        ),
        fat_g=Estimate(
            nutrient="fat",
            estimate=response_content_json["fat_g"]["estimate"],
            units=response_content_json["fat_g"]["units"],
            confidence=response_content_json["fat_g"]["confidence"],
        ),
        carbs_g=Estimate(
            nutrient="carbs",
            estimate=response_content_json["carbs_g"]["estimate"],
            units=response_content_json["carbs_g"]["units"],
            confidence=response_content_json["carbs_g"]["confidence"],
        ),
        micronutrients=[_format_estimate(
            m) for m in response_content_json["micronutrients"]],
        notes=notes,
    )


def _format_estimate(estimate_json: dict) -> Estimate:
    return Estimate(
        nutrient=estimate_json["nutrient"],
        estimate=estimate_json["estimate"],
        units=estimate_json["units"],
        confidence=estimate_json["confidence"])


if __name__ == "__main__":
    handle_user_input("It's my last meal of the day, what should I eat?")
