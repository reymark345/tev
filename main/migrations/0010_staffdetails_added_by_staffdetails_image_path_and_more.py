# Generated by Django 4.1 on 2024-04-23 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_transactionlogs_tevincoming_is_latest'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffdetails',
            name='added_by',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='staffdetails',
            name='image_path',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='staffdetails',
            name='middle_initial',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
