import graphene


class AddRecipeResponseGraphql(graphene.ObjectType):
    recipe_id = graphene.Int()
