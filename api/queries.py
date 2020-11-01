import re
from urllib.parse import urlparse

import graphene

from collections import Counter

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Prefetch
from graphene import ObjectType

from graphene_django.types import DjangoObjectType

from api.domain import create_recipe_from_url, save_recipe_from_parsed_recipes
from api.models import Ingredient, Recipe, RecipeIngredient, PantryIngredient, Pantry, \
    IngredientToIngredient
from api.mutations import UserType


class SimpleIngredientType(ObjectType):
    id = graphene.Int()
    name = graphene.String()


class IngredientType(DjangoObjectType):
    class Meta:
        model = Ingredient

    categories_list = graphene.String()

    def resolve_categories_list(self, info):
        categories = [i.parent.name for i in IngredientToIngredient.objects.filter(
            child_id=self.id).prefetch_related('parent')]

        return ', '.join(categories)

    categories = graphene.List(SimpleIngredientType)

    def resolve_categories(self, info):
        parents = [i.parent for i in IngredientToIngredient.objects.filter(
            child_id=self.id).prefetch_related('parent')]
        return [{
            'id': parent.id,
            'name': parent.name
        } for parent in parents]


class RecipeIngredientType(DjangoObjectType):
    class Meta:
        model = RecipeIngredient


class RecipeType(DjangoObjectType):
    class Meta:
        model = Recipe

    source_or_url = graphene.String()

    def resolve_source_or_url(self, info):
        if self.source:
            return self.source
        elif self.source_url:
            return urlparse(self.source_url).netloc.split('.')[0]
        return ''

    all_ingredients = graphene.List(graphene.String)

    def resolve_all_ingredients(self, info):
        return [str(i) for i in self.recipeingredient_set.all() if not i.ingredient.is_garnish]

    ingredients_text = graphene.String()

    def resolve_ingredients_text(self, info):
        missing = set()
        if hasattr(self, 'missing_ingredient_models'):
            missing = {m.name for m in self.missing_ingredient_models}
        return ', '.join(i.name for i in self.ingredient_list
                         if not i.is_garnish and i.name not in missing)

    garnishes = graphene.List(graphene.String)

    def resolve_garnishes(self, info):
        return [i for i in self.recipeingredient_set.all() if i.ingredient.is_garnish]

    missing_ingredients = graphene.String()

    def resolve_missing_ingredients(self, info):
        if not hasattr(self, 'missing_ingredient_models'):
            return None
        else:
            return ', '.join(ingredient.name for ingredient in self.missing_ingredient_models)


class PantryIngredientType(DjangoObjectType):
    class Meta:
        model = PantryIngredient


def _filter_on_pantry(current_filtered, user, allowances=0):
    filtered = []

    pantry = Pantry.objects.filter(owner=user).first()
    pantry_ingredients = PantryIngredient.objects\
        .filter(pantry=pantry, in_stock=True).select_related('ingredient').order_by('-id')
    ingredients = [pi.ingredient for pi in pantry_ingredients]

    ids = {p.id for p in ingredients}
    names = [p.name for p in ingredients]
    for recipe in current_filtered:
        missing_ingredients = []
        in_pantry = True
        current_allowances = allowances
        for ingredient in recipe.recipeingredient_set.all():
            if (
                not ingredient.ingredient.is_garnish
                and ingredient.ingredient.id not in ids
                and ingredient.ingredient.name not in names
            ):
                missing_ingredients.append(ingredient.ingredient)
                if not current_allowances:
                    in_pantry = False
                    break
                else:
                    current_allowances -= 1

        # in_pantry = not any(
        #     ingredient.ingredient.id not in ids and ingredient.ingredient.name not in names
        #     for ingredient in recipe.recipeingredient_set.all()
        #     if not ingredient.ingredient.is_garnish
        # )
        if missing_ingredients:
            recipe.missing_ingredient_models = missing_ingredients
        if in_pantry:
            filtered.append(recipe)
    return filtered


class Query(object):
    all_ingredients = graphene.List(IngredientType)

    def resolve_all_ingredients(self, info, **kwargs):
        return Ingredient.objects.all()

    all_ingredients_not_garnish = graphene.List(IngredientType)

    def resolve_all_ingredients_not_garnish(self, info, **kwargs):
        return Ingredient.objects.filter(is_garnish=False)

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

    searched_recipes = graphene.List(RecipeType,
                                     search_term=graphene.String(required=False),
                                     allowances=graphene.Int(required=False),
                                     shortlist=graphene.Boolean(required=False))

    def resolve_searched_recipes(self, info, search_term=None, allowances=0, shortlist=False):
        print(search_term)
        # TODO: add ability for multiple search filters via commas or semicolons
        def get_in_quotes_and_whats_left(text):
            found = re.findall('"([^"]*)"', text)
            left = re.sub('"([^"]*)"', '', text)
            return found, left

        # handle possible url
        validator = URLValidator()
        try:
            validator(search_term)
        except ValidationError:
            pass
        else:
            # add new recipe and search on all
            recipe = create_recipe_from_url(search_term)
            save_recipe_from_parsed_recipes(recipe)
            search_term = ''

        vectors = SearchVector('name', config='english_unaccent') + \
                  SearchVector('ingredients__name', config='english_unaccent') + \
                  SearchVector('source', config='english_unaccent')

        exact_ids = None
        if not search_term:
            current_filtered = Recipe.objects.all()\
                .prefetch_related(
                    Prefetch('ingredients', to_attr='ingredient_list',
                             queryset=Ingredient.objects.all().only('name', 'is_garnish')))\
                .order_by('-id')\
                .only('id', 'source', 'source_url', 'name', 'shortlist', 'rating', 'non_alcoholic')
        else:
            recipes = Recipe.objects.all().prefetch_related(
                    Prefetch('ingredients', to_attr='ingredient_list',
                             queryset=Ingredient.objects.all().only('name', 'is_garnish')))

            if '"' in search_term:
                if Counter(search_term)['"'] % 2 != 0:
                    return None

                exact_matches, non_exact = get_in_quotes_and_whats_left(search_term)
                search_term = non_exact.strip()
                if exact_matches:
                    exact_ids = set()
                    for match in exact_matches:
                        recipes = Recipe.objects.all()
                        if exact_ids:
                            recipes.filter(id__in=exact_ids)
                        recipes = recipes.annotate(search=vectors)\
                            .filter(search=SearchQuery(match, search_type='phrase',
                                                       config='english_unaccent'))
                        if exact_ids:
                            exact_ids = exact_ids & set(recipes.values_list('id', flat=True))
                        else:
                            exact_ids = set(recipes.values_list('id', flat=True))

            ids = recipes.annotate(search=vectors)\
                .filter(search__icontains=search_term)\
                .values_list('id', flat=True)

            search_terms = search_term.split()
            # if we want to filter on individual terms using OR
            # my_filter = search_term
            # if search_terms:
            #     my_filter = SearchQuery(search_terms.pop())
            #     for t in search_terms:
            #         my_filter &= SearchQuery(t)

            extra_ids = []
            for term in search_terms:
                extra = Recipe.objects.annotate(search=vectors)\
                    .filter(search__icontains=term).values_list('id', flat=True)
                extra_ids += extra

            final_ids = Recipe.objects\
                .annotate(search=vectors)\
                .filter(search=SearchQuery(search_term)).values_list('id', flat=True)

            ids = set(ids) | set(extra_ids) | set(final_ids)
            if exact_ids:
                ids = ids & exact_ids
            current_filtered = Recipe.objects.filter(id__in=ids)\
                .prefetch_related(
                    Prefetch('ingredients', to_attr='ingredient_list',
                             queryset=Ingredient.objects.all()
                .only('name', 'is_garnish'))).order_by('-id')
        if shortlist:
            current_filtered = current_filtered.filter(shortlist=True)
        if allowances != -1:
            # TODO: add auth!
            current_filtered = _filter_on_pantry(current_filtered, User.objects.first(),
                                                 allowances=allowances)
        return current_filtered

    recipe = graphene.Field(RecipeType, recipe_id=graphene.Int(required=True))

    def resolve_recipe(self, info, recipe_id):
        return Recipe.objects.filter(id=recipe_id).prefetch_related('ingredients').first()

    users_pantry = graphene.List(PantryIngredientType, id=graphene.Int(required=True))

    def resolve_users_pantry(self, info, id):
        # owner = User.objects.get(id=1)
        # TODO: setup login!!!

        try:
            pantry = Pantry.objects.filter(owner_id=1).prefetch_related('pantry_ingredients').first()
            return pantry.pantry_ingredients.filter(ingredient__is_garnish=False)
        except AttributeError:
            return []

    # TODO: add pantry filter search

    filtered_ingredients = graphene.List(IngredientType,
                                         is_garnish=graphene.Boolean(required=False),
                                         search_term=graphene.String(required=False))

    def resolve_filtered_ingredients(self, info, is_garnish=False, search_term=None):
        if search_term is None:
            return Ingredient.objects.filter(is_garnish=is_garnish)

        filtered = Ingredient.objects.filter(is_garnish=is_garnish)
        filtered = filtered.filter(name__icontains=search_term)
        return filtered

    get_ingredient = graphene.Field(IngredientType, id=graphene.Int(required=True))

    def resolve_get_ingredient(self, info, id):
        return Ingredient.objects.get(id=id)