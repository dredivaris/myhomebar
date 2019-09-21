from api.validators import RecipeValidator


def create_recipe(self, args, user):
    recipe_validator = RecipeValidator(**args)
    print('init validator')
    recipe_validator.with_user(user)
    print('set user')
    recipe_validator.validate()
    recipe_validator.save()
