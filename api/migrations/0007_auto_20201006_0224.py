# Generated by Django 2.2.5 on 2020-10-06 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_ingredientmapping_pantry_pantryingredient'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='date_added',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='date_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
