# Generated by Django 4.2.20 on 2025-05-05 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0035_systemconfiguration_is_travel_expire'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfiguration',
            name='days_expire',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
