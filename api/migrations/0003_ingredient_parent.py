# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-04 00:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20190304_0011'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingredient',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.Ingredient'),
        ),
    ]