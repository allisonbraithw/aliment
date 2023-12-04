"""Contains Types and helpers for generating nutrition plans."""
from pydantic import BaseModel
from typing import List
from enum import Enum

# region Types

class Sex(Enum):
    MALE = "male"
    FEMALE = "female"
    
class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    
class GoalCategory(Enum):
    MAINTAIN = "maintain"
    LOSE = "lose"
    GAIN = "gain"
    
class Goal(BaseModel):
    category: GoalCategory
    description: str
    

# Basic user object containing relevant information for generating a nutrition plan
class UserProfileModel(BaseModel):
    name: str
    age: int
    height: int
    weight: int
    sex: Sex
    activity_level: ActivityLevel
    goal: Goal
    
class MicronutrientGoal(BaseModel):
    nutrient: str
    goal: int
    units: str
    
class Status(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    
class NutritionPlanModel(BaseModel):
    start_date: str
    end_date: str
    status: Status
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    micronutrient_goals: List[MicronutrientGoal]
    
# endregion

class NutritionPlanGenerator:
    """Generates a nutrition plan based on a user profile."""
    def __init__(self, user_profile: UserProfileModel):
        self.user_profile = user_profile
        
    def generate_base_plan(self) -> NutritionPlanModel:
        """Generates a nutrition plan based on the user profile."""
        # calculate calories based on height, weight, age, gender, goal
        # calculate macros based on calories and goal, nudge to keto as needed
        # calcuate micronutrient goals based on heigh, age, gender
        pass
        
    def _calculate_calories(self) -> int:
        """Calculates the number of calories the user should consume per day."""
        # https://www.calculator.net/calorie-calculator.html
        # https://www.calculator.net/bmr-calculator.html
        # https://www.calculator.net/calorie-calculator.html
        pass
        
    def _calculate_macros(self) -> int:
        """Calculates the number of macros the user should consume per day."""
        # https://www.calculator.net/macro-calculator.html
        pass
    
    def _calculate_micronutrient_goals(self) -> List[MicronutrientGoal]:
        """Calculates the micronutrient goals the user should consume per day."""
        # https://www.calculator.net/macro-calculator.html
        pass
        