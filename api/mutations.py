import graphene
from graphql import GraphQLError

from api.domain import create_recipe
from api.types import AddRecipeResponseGraphql

from django.contrib.auth import get_user_model

from graphene_django import DjangoObjectType


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    def mutate(self, info, username, password, email, first_name='', last_name=''):
        user = get_user_model()(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user)


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
        print('currently logged in user is', info.context.user)
        from pprint import pprint
        pprint(args)
        create_recipe(args, info.context.user)


class Mutation(object):
    add_recipe = AddRecipe.Field()
    create_user = CreateUser.Field()
