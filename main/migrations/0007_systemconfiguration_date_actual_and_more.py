# Generated by Django 4.2.1 on 2024-03-24 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_tevincoming_date_reviewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfiguration',
            name='date_actual',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='systemconfiguration',
            name='date_limit',
            field=models.BooleanField(default=True),
        ),
    ]
