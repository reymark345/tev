# Generated by Django 4.0.2 on 2023-09-06 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tevoutgoing',
            name='out_by',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]