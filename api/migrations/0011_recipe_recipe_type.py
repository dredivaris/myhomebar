# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-25 02:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_auto_20190325_0215'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='recipe_type',
            field=models.CharField(choices=[('COCKTAIL', 'Cocktail'), ('SYRUP', 'Syrup'), ('CORDIAL', 'Cordial'), ('BITTERS', 'Bitters'), ('OTHER', 'Other')], default='COCKTAIL', max_length=20),
        ),
    ]
