import graphene
from django.contrib.auth import get_user_model

from graphene_django.types import DjangoObjectType

from api.models import Ingredient, Recipe
from api.mutations import UserType


class IngredientType(DjangoObjectType):
    class Meta:
        model = Ingredient


class RecipeType(DjangoObjectType):
    class Meta:
        model = Recipe


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
        # import pdb
        # pdb.set_trace()
        if user.is_anonymous:
            raise Exception('Not logged in!')

        return user

    users_recipes = graphene.List(RecipeType)

    def resolve_users_recipes(self, info, user_id):
        return self.users_recipes
