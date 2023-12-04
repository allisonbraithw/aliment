import graphene
import time
from graphene_pydantic import PydanticObjectType
from aliment.nutrition.plan import NutritionPlanModel, UserProfileModel, NutritionPlanGenerator
from aliment.nutrition.log import handle_user_input
from graphene_federation import build_schema

# region Types
class NutritionPlan(PydanticObjectType):
    class Meta:
        model = NutritionPlanModel

class UserProfile(PydanticObjectType):
    class Meta:
        model = UserProfileModel        


# endregion

# region Mutations
class CreateNutritionPlan(graphene.Mutation):
    class Arguments:
        user_profile = graphene.Field(UserProfile)
        
    plan = graphene.Field(NutritionPlan)
        
    def mutate(self, info, user_profile):
        plan = NutritionPlanGenerator(user_profile=user_profile).generate_base_model()
        # TODO(arb) write to DB
        return CreateNutritionPlan(user_profile=user_profile, plan=plan)
    
class ChatResponse(graphene.Mutation):
    class Arguments:
        user_input = graphene.String()
        
    response = graphene.String()
        
    def mutate(self, info, user_input):
        log_entry = handle_user_input(datetime=time.now(), notes=user_input)
        # TODO(arb) write to DB
        return ChatResponse(response=log_entry)

# endregion

# region Schema
class Mutation(graphene.ObjectType):
    create_nutrition_plan = CreateNutritionPlan.Field()
    log_meal = ChatResponse.Field()

class Query(graphene.ObjectType):
    pass

schema = build_schema(query=Query, mutation=Mutation)

# endregion