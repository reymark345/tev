# Generated by Django 4.0.2 on 2023-09-06 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_tevoutgoing_out_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='tevoutgoing',
            name='is_print',
            field=models.BooleanField(default=False),
        ),
    ]