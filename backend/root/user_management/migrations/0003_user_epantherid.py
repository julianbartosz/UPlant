# Generated by Django 5.0.4 on 2024-05-16 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0002_remove_user_epantherid'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='epantherid',
            field=models.CharField(default='jbartosz', max_length=20, verbose_name='ePanther ID'),
        ),
    ]