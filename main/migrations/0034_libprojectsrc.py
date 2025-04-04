# Generated by Django 4.2.19 on 2025-03-19 14:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0033_alter_farematrix_hire_rate_one_way_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LibProjectSrc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('cluster_id', models.IntegerField()),
                ('is_active', models.IntegerField()),
                ('is_primary', models.IntegerField()),
                ('created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('updated_by', models.IntegerField()),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'lib_project_src',
                'managed': True,
            },
        ),
    ]
