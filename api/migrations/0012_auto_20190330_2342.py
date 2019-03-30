# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-30 23:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_recipe_recipe_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='source',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='source_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
