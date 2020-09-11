from api.validators import RecipeValidator


def create_recipe(data, user):
    recipe_validator = RecipeValidator(**data)
    recipe_validator.with_user(user)
    recipe_validator.validate()
    recipe_validator.save()


def tokenize_recipes_from_plaintext(text):
    lines = text.split('\n')
    recipe_texts = []
    current_lines = []
    blank_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            blank_lines += 1

        if not current_lines:
            if line:
                current_lines.append(line)
                blank_lines = 0
        elif blank_lines > 1:
            recipe_texts.append('\n'.join(current_lines))
            current_lines = []
        else:
            if line:
                current_lines.append(line)
    if current_lines:
        recipe_texts.append('\n'.join(current_lines))

    # TODO: here we want to parse individual recipes
    return recipe_texts

def create_recipes_from_plaintext(text):
    pass