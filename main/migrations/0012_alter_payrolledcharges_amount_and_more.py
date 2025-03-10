# Generated by Django 4.1 on 2024-06-14 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_remove_tevincoming_is_latest_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payrolledcharges',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=10, default=0, max_digits=30, null=True),
        ),
        migrations.AlterField(
            model_name='tevincoming',
            name='date_reviewed',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
