# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-25 02:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_auto_20190325_0214'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Beverage',
            new_name='Recipe',
        ),
    ]
