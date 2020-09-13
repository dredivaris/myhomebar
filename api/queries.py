import graphene
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector
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

    all_ingredients = graphene.List(graphene.String)

    def resolve_all_ingredients(self, info):
        return [str(i) for i in self.recipeingredient_set.all() if not i.ingredient.is_garnish]

    ingredients_text = graphene.String()

    def resolve_ingredients_text(self, info):
        return ', '.join(i.name for i in self.ingredients.all() if not i.is_garnish)

    garnishes = graphene.List(graphene.String)

    def resolve_garnishes(self, info):
        return [i for i in self.recipeingredient_set.all() if i.ingredient.is_garnish]


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
        return Recipe.objects.filter(
            owner=user, recipe_type=Recipe.COCKTAIL
        ).prefetch_related(
            Prefetch(
                'recipeingredient_set',
                queryset=ri_query,
                to_attr='ingredients_set',
            )
        )

    users_recipe = graphene.Field(RecipeType, id=graphene.Int(required=True))

    def resolve_users_recipe(self, info, id):
        return Recipe.objects.get(pk=id)

    searched_recipes = graphene.List(RecipeType, search_term=graphene.String(required=False))

    def resolve_searched_recipes(self, info, search_term=None):
        # TODO: add ability for multiple search filters via commas or semicolons
        if not search_term:
            return Recipe.objects.all().prefetch_related('ingredients')

        ids = Recipe.objects\
            .annotate(search=SearchVector('name') + SearchVector('ingredients__name'))\
            .filter(search=search_term).values_list('id', flat=True)

        ids = set(ids)
        return Recipe.objects.filter(id__in=ids).prefetch_related('ingredients')

    recipe = graphene.Field(RecipeType, recipe_id=graphene.Int(required=True))

    def resolve_recipe(self, info, recipe_id):
        return Recipe.objects.filter(id=recipe_id).prefetch_related('ingredients').first()