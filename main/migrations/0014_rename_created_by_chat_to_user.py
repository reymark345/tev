# Generated by Django 4.1 on 2024-06-21 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_chat'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='created_by',
            new_name='to_user',
        ),
    ]