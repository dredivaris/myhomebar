import graphene
from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from graphene_django.types import DjangoObjectType

from api.models import Ingredient, Recipe, RecipeIngredient
from api.mutations import UserType


class IngredientType(DjangoObjectType):
    class Meta:
        model = Ingredient


class RecipeIngredientType(DjangoObjectType):
    class Meta:
        model = RecipeIngredient


class RecipeType(DjangoObjectType):
    class Meta:
        model = Recipe

    ingredients = graphene.List(graphene.String)

    def resolve_ingredients(self, info):
        return self.ingredients_set


class Query(object):
    all_ingredients = graphene.List(IngredientType)

    def resolve_all_ingredients(self, info, **kwargs):
        return Ingredient.objects.all()

    users = graphene.List(UserType)

    def resolve_users(self, info):
        return get_user_model().objects.all()

    me = graphene.Field(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        return user

    users_recipes = graphene.List(RecipeType)

    def resolve_users_recipes(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        ri_query = RecipeIngredient.objects.select_related('ingredient', 'quantity__unit')
        recipes = Recipe.objects.filter(
            owner=user,
            recipe_type=Recipe.COCKTAIL
        ).prefetch_related(
            Prefetch('recipeingredient_set', queryset=ri_query, to_attr='ingredients_set')
        )
        # print(f'recipes for user {user} are {recipes}, len tot {Recipe.objects.count()}')
        return recipes

    users_recipe = graphene.Field(RecipeType, id=graphene.Int(required=True))

    def resolve_users_recipe(self, info, id):
        return Recipe.objects.get(pk=id)
