import graphene
from graphql import GraphQLError

from api.types import AddRecipeResponseGraphql
from api.validators import RecipeValidator


class AddRecipe(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        recipe_type = graphene.String(required=True)
        ingredients = graphene.String(required=True)
        directions = graphene.String(required=True)
        rating = graphene.Float()
        rating_set = graphene.Boolean()
        glassware = graphene.String()
        tools = graphene.String()
        garnish = graphene.String()
        description = graphene.String()
        notes = graphene.String()
        source = graphene.String()
        source_url = graphene.String()
        attribution = graphene.String()

    Output = AddRecipeResponseGraphql

    def mutate(self, info, **args):
        from pprint import pprint
        pprint(args)
        recipe_validator = RecipeValidator(**args)
        recipe_validator.validate()
        recipe_validator.save()

class Mutation(object):
    add_recipe = AddRecipe.Field()
