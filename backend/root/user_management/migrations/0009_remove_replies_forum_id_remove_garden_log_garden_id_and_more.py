# Generated by Django 5.0.4 on 2025-03-26 21:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0008_remove_user_is_deleted_user_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='replies',
            name='forum_id',
        ),
        migrations.RemoveField(
            model_name='garden_log',
            name='garden_id',
        ),
        migrations.RemoveField(
            model_name='garden_log',
            name='plant_id',
        ),
        migrations.RemoveField(
            model_name='gardens',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='likes',
            name='reply_id',
        ),
        migrations.RemoveField(
            model_name='likes',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='replies',
            name='parent_id',
        ),
        migrations.RemoveField(
            model_name='replies',
            name='user_id',
        ),
        migrations.DeleteModel(
            name='Forums',
        ),
        migrations.DeleteModel(
            name='Garden_log',
        ),
        migrations.DeleteModel(
            name='Plants',
        ),
        migrations.DeleteModel(
            name='Gardens',
        ),
        migrations.DeleteModel(
            name='Likes',
        ),
        migrations.DeleteModel(
            name='Replies',
        ),
    ]
