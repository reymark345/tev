# Generated by Django 4.1 on 2024-03-14 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rename_division_id_tevincoming_division_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tevincoming',
            name='reviewed_by',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
