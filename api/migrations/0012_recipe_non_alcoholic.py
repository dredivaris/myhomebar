# Generated by Django 2.2.5 on 2020-10-19 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_recipeingredient_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='non_alcoholic',
            field=models.BooleanField(default=False),
        ),
    ]
