import graphene


class AddRecipeResponseGraphql(graphene.ObjectType):
    recipe_id = graphene.Int()


class DeleteRecipeResponseGraphql(graphene.ObjectType):
    deleted = graphene.Boolean()


class AddRecipesFromTextResponseGraphql(graphene.ObjectType):
    recipe_ids = graphene.List(graphene.Int)


class LinkOrCreateIngredientsForPantryResponseGraphql(graphene.ObjectType):
    ingredient_ids = graphene.List(graphene.Int)


class AddRecipeFlexibleResponseGraphql(graphene.ObjectType):
    recipe_id = graphene.Int()


class IngredientBulkUpdateResponseGraphql(graphene.ObjectType):
    count = graphene.Int()


class IngredientCreateResponseGraphql(graphene.ObjectType):
    created = graphene.Boolean()


class ToggleStockResponseGraphql(graphene.ObjectType):
    toggled_to = graphene.Boolean()


class EditIngredientFlexibleResponseGraphql(graphene.ObjectType):
    added = graphene.Boolean()