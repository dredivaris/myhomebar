import json

import graphene
import requests
from django.db import IntegrityError

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from graphene_file_upload.scalars import Upload

from api.domain import create_recipe, create_recipe_from_plaintext, save_recipe_from_parsed_recipes, \
    tokenize_recipes_from_plaintext, update_recipe, merge_ingredients_and_update_models
from api.models import Pantry, Ingredient, PantryIngredient, IngredientToIngredient
from api.types import AddRecipeResponseGraphql, AddRecipesFromTextResponseGraphql, \
    LinkOrCreateIngredientsForPantryResponseGraphql, AddRecipeFlexibleResponseGraphql, \
    IngredientBulkUpdateResponseGraphql, IngredientCreateResponseGraphql, \
    ToggleStockResponseGraphql, EditIngredientFlexibleResponseGraphql

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
        Pantry.objects.create(owner=user)

        return CreateUser(user=user)


class AddRecipeFlexible(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String()
        ingredients = graphene.String()
        directions = graphene.String()
        rating = graphene.Float()
        glassware = graphene.String()
        garnish = graphene.String()
        description = graphene.String()
        notes = graphene.String()
        source = graphene.String()
        source_url = graphene.String()
        shortlist = graphene.Boolean()

    Output = AddRecipeFlexibleResponseGraphql

    def mutate(self, info, **args):
        owner = User.objects.first()  # todo: add auth
        print(f'received data from {args}')
        args['recipe_type'] = 'COCKTAIL'
        args_to_del = []
        for argument, value in args.items():
            if type(value) is str:
                value = value.strip()
            if not value and type(value) is not bool:
                args_to_del.append(argument)

        for arg in args_to_del:
            del args[arg]
        if 'source' in args:
            validator = URLValidator()

            try:
                validator(args['source'])
            except ValidationError:
                pass
            else:
                args['source_url'] = args['source']
                del args['source']

        update_recipe(args, owner)

        return AddRecipeFlexibleResponseGraphql(1)


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


class AddRecipesFromText(graphene.Mutation):
    class Arguments:
        recipe_text = graphene.String(required=True)

    Output = AddRecipesFromTextResponseGraphql

    def mutate(self, info, recipe_text):
        print(f'text received: {recipe_text}')
        recipes = tokenize_recipes_from_plaintext(recipe_text)
        print(recipes)
        recipes_saved_ids = []
        for recipe in recipes:
            # TODO: validate not an existing recipe
            recipes_saved_ids.append(save_recipe_from_parsed_recipes(recipe))

        return AddRecipesFromTextResponseGraphql(recipe_ids=recipes_saved_ids)


class ConvertImageToRecipeText(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)
        file_type = graphene.String(required=True)
    text = graphene.String()

    def mutate(self, info, file, file_type, **kwargs):

        # first convert / rezise image
        from PIL import Image
        import io
        import base64
        base64_file = base64.b64decode(file)

        to_file_type = {
            'image/jpeg': 'JPG',
            'image/png': 'PNG'
        }
        ocr_filetype = to_file_type[file_type]

        image = Image.open(io.BytesIO(base64_file))
        # new_image = image.rotate(180)
        image.save('testimage_blahblah.jpeg', format='JPEG', quality=50, optimize=True)
        with io.BytesIO() as output:
            image.save(output, quality=70, optimize=True, format="JPEG")
            contents = output.getvalue()
        contents = base64.b64encode(contents).decode("utf-8")

        # rapidapi version
        # url = "https://ocr-supreme.p.rapidapi.com/ocr/image"
        # payload = json.dumps({
        #     'data': contents, 'output': 'text'
        # })
        # headers = {
        #     'x-rapidapi-host': "ocr-supreme.p.rapidapi.com",
        #     'x-rapidapi-key': "d77898db4bmsh5f47bec815d12fbp138d95jsn4947265a4033",
        #     'content-type': "application/json",
        #     'accept': "application/json"
        # }
        #
        # response = requests.request("POST", url, data=payload, headers=headers)
        # text = response.json()['data']
        # print(response.text)

        url = 'https://api.ocr.space/parse/image'
        apikey = '4253b0659088957'
        base64Image = contents
        ocrEngine = '1'

        headers = {
            'apikey': apikey
        }
        payload = {
            # 'file': file,
            'base64image': f'data:{file_type};base64,' + base64Image,
            'ocrEngine': ocrEngine,
            'filetype': ocr_filetype
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        cont = response.json()
        print(cont)
        return ConvertImageToRecipeText(text=cont['ParsedResults'][0]['ParsedText'])


class LinkOrCreateIngredientsForPantry(graphene.Mutation):
    class Arguments:
        ingredients = graphene.List(graphene.String, required=True)

    Output = LinkOrCreateIngredientsForPantryResponseGraphql

    def mutate(self, info, ingredients):
        print(f'text received: {ingredients}')
        existing_ingredient_ids, new_ingredient_texts = [], []

        pantry = Pantry.objects.get(owner_id=1)  # TODO: implement proper login!
        for id_or_new_ingredient in ingredients:
            if id_or_new_ingredient.isnumeric():
                existing_ingredient_ids.append(int(id_or_new_ingredient))
            else:
                new_ingredient_texts.append(id_or_new_ingredient)

        new_ingredient_ids = []
        if new_ingredient_texts:
            for new_ingredient in new_ingredient_texts:
                ingredient = Ingredient.objects.create(
                    name=new_ingredient,
                    owner_id=1,  # TODO: implement proper login!
                    is_garnish=False
                )
                new_ingredient_ids.append(ingredient.id)

        ids_to_add = new_ingredient_ids + existing_ingredient_ids

        PantryIngredient.objects.bulk_create([
            PantryIngredient(pantry=pantry, ingredient_id=i) for i in ids_to_add
        ])

        return LinkOrCreateIngredientsForPantryResponseGraphql(ingredient_ids=ids_to_add)


'''
web        | {'attribution': 'Jimbo',
web        |  'directions': 'one \ntwo\nthree',
web        |  'garnish': 'flower',
web        |  'glassware': 'coupe',
web        |  'ingredients': 'one\ntwo and \nthree',
web        |  'name': 'dre',
web        |  'notes': 'afasf',
web        |  'rating': 0.0,
web        |  'rating_set': False,
web        |  'recipe_type': 'COCKTAIL',
web        |  'source': 'rad',
web        |  'source_url': '',
web        |  'tools': 'grinder'}
'''


class IngredientBulkUpdate(graphene.Mutation):
    class Arguments:
        ids = graphene.List(graphene.Int)
        names = graphene.List(graphene.String)

    Output = IngredientBulkUpdateResponseGraphql

    def mutate(self, info, ids, names):
        if len(names) != len(ids):
            return IngredientBulkUpdateResponseGraphql(count=0)
        counts = 0
        for _id, name in zip(ids, names):
            try:
                counts += Ingredient.objects.filter(id=_id).update(name=name)
            except IntegrityError:
                merge_ingredients_and_update_models(_id, name)
        return IngredientBulkUpdateResponseGraphql(count=counts)


class IngredientCreate(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        is_garnish = graphene.Boolean(required=True)
        add_to_pantry = graphene.Boolean(required=False)

    Output = IngredientCreateResponseGraphql

    def mutate(self, info, name, is_garnish, add_to_pantry=False):
        if Ingredient.objects.filter(name=name).count():
            return IngredientCreateResponseGraphql(created=False)

        # TODO: handle auth
        ingredient = Ingredient.objects.create(name=name.title(),
                                               is_garnish=is_garnish,
                                               owner=User.objects.first())
        if add_to_pantry:
            # TODO: add auth
            pantry = Pantry.objects.get(owner=User.objects.first())
            PantryIngredient.objects.create(pantry=pantry, ingredient=ingredient)
        return IngredientCreateResponseGraphql(created=True)


class ToggleStock(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    Output = ToggleStockResponseGraphql

    def mutate(self, info, id):
        # TODO: add auth
        pi = PantryIngredient.objects.get(id=id)
        pi.in_stock = not pi.in_stock
        pi.save()
        return ToggleStockResponseGraphql(toggled_to=pi.in_stock)


class EditIngredientFlexible(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=True)
        categories = graphene.List(graphene.String, required=True)
        is_garnish = graphene.Boolean()
        is_generic = graphene.Boolean()
        add_to_pantry = graphene.Boolean()

    Output = EditIngredientFlexibleResponseGraphql

    def mutate(self, info, id, name, categories,
               is_garnish=None, is_generic=None, add_to_pantry=None):

        owner = User.objects.first()  # todo: add auth
        ingredient = Ingredient.objects.get(id=id)
        ingredient.name = name
        if is_garnish is not None:
            ingredient.is_garnish = is_garnish
        if is_generic is not None:
            ingredient.is_generic = is_generic

        ingredient.save()

        if add_to_pantry:
            try:
                PantryIngredient.objects.get(ingredient=ingredient, pantry__owner=owner)
            except PantryIngredient.DoesNotExist:
                PantryIngredient.objects.create(
                    ingredient=ingredient, pantry__owner=owner, in_stock=True)

        categories = [int(c) for c in categories if c]
        existings = IngredientToIngredient.objects.filter(child=ingredient)
        for existing in existings:
            if existing.parent_id not in categories:
                existing.delete()

        if categories:
            for category in categories:
                IngredientToIngredient.objects.get_or_create(child=ingredient, parent_id=category)

        return EditIngredientFlexibleResponseGraphql(True)


class Mutation(object):
    add_recipe = AddRecipe.Field()
    add_recipe_flexible = AddRecipeFlexible.Field()
    create_user = CreateUser.Field()
    add_recipes_from_text = AddRecipesFromText.Field()
    link_or_create_ingredients_for_pantry = LinkOrCreateIngredientsForPantry.Field()
    convert_image_to_recipe_text = ConvertImageToRecipeText.Field()
    ingredient_bulk_update = IngredientBulkUpdate.Field()
    create_ingredient = IngredientCreate.Field()
    toggle_stock = ToggleStock.Field()
    edit_ingredient_flexible = EditIngredientFlexible.Field()
