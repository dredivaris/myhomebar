import graphene

from graphene_django.types import DjangoObjectType

from api.models import Ingredient


class IngredientType(DjangoObjectType):
    class Meta:
        model = Ingredient


class Query(object):
    all_ingredients = graphene.List(IngredientType)

    def resolve_all_ingredients(self, info, **kwargs):
        return Ingredient.objects.all()
