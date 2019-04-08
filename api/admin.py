from django.contrib import admin

# Register your models here.
from api.models import Ingredient, Recipe, Unit, Quantity, RecipeIngredient


class RecipeAdmin(admin.ModelAdmin):
    model = Recipe
    filter_horizontal = ('ingredients', )


admin.site.register(Ingredient)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Unit)
admin.site.register(Quantity)
admin.site.register(RecipeIngredient)
