# Generated by Django 5.1.3 on 2025-01-21 23:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_alter_category_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expense',
            options={'ordering': ['-date']},
        ),
    ]
