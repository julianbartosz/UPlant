# Generated by Django 5.0.4 on 2025-03-06 23:33

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0005_plants_replies_remove_user_address_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forums',
            options={'verbose_name': 'forum', 'verbose_name_plural': 'forums'},
        ),
        migrations.AlterModelOptions(
            name='garden_log',
            options={'verbose_name': 'garden log', 'verbose_name_plural': 'garden logs'},
        ),
        migrations.AlterModelOptions(
            name='gardens',
            options={'verbose_name': 'garden', 'verbose_name_plural': 'gardens'},
        ),
        migrations.AlterModelOptions(
            name='likes',
            options={'verbose_name': 'like', 'verbose_name_plural': 'likes'},
        ),
        migrations.AlterModelOptions(
            name='plants',
            options={'verbose_name': 'plant', 'verbose_name_plural': 'plants'},
        ),
        migrations.AlterModelOptions(
            name='replies',
            options={'verbose_name': 'reply', 'verbose_name_plural': 'replies'},
        ),
        migrations.RemoveConstraint(
            model_name='garden_log',
            name='check_x_coor_pos',
        ),
        migrations.RemoveConstraint(
            model_name='garden_log',
            name='check_y_coor_pos',
        ),
        migrations.RemoveConstraint(
            model_name='plants',
            name='check_maturity_pos',
        ),
        migrations.RemoveConstraint(
            model_name='plants',
            name='check_germ_pos',
        ),
        migrations.RemoveConstraint(
            model_name='plants',
            name='check_spacing_x_pos',
        ),
        migrations.RemoveConstraint(
            model_name='plants',
            name='check_spacing_y_pos',
        ),
        migrations.RemoveField(
            model_name='user',
            name='first_name',
        ),
        # migrations.RemoveField(
        #     model_name='user',
        #     name='is_active',
        # ),
        migrations.RemoveField(
            model_name='user',
            name='last_name',
        ),
        migrations.AddField(
            model_name='gardens',
            name='name',
            field=models.CharField(blank=True, max_length=25, null=True, verbose_name='garden name'),
        ),
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=50, null=True, unique=True, verbose_name='username'),
        ),
        migrations.AlterField(
            model_name='forums',
            name='body',
            field=models.TextField(verbose_name='body'),
        ),
        migrations.AlterField(
            model_name='forums',
            name='title',
            field=models.CharField(max_length=50, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='garden_log',
            name='planted_date',
            field=models.DateField(default=datetime.date.today, verbose_name='date planted'),
        ),
        migrations.AlterField(
            model_name='garden_log',
            name='x_coordinate',
            field=models.PositiveIntegerField(verbose_name='x-coordinate location'),
        ),
        migrations.AlterField(
            model_name='garden_log',
            name='y_coordinate',
            field=models.PositiveIntegerField(verbose_name='y-coordinate location'),
        ),
        migrations.AlterField(
            model_name='gardens',
            name='size_x',
            field=models.PositiveIntegerField(verbose_name='garden length'),
        ),
        migrations.AlterField(
            model_name='gardens',
            name='size_y',
            field=models.PositiveIntegerField(verbose_name='garden width'),
        ),
        migrations.AlterField(
            model_name='likes',
            name='ld_value',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='likes',
            name='reply_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_management.replies'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='germination_time',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='germination time'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='maturity_time',
            field=models.PositiveIntegerField(verbose_name='maturity time'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='plant_description',
            field=models.TextField(blank=True, null=True, verbose_name='plant description'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='planting_depth',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name='planting depth'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='spacing_x',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='spacing length'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='spacing_y',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='spacing width'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='species',
            field=models.CharField(max_length=50, verbose_name='species'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='sun_level',
            field=models.CharField(blank=True, choices=[('full sun', 'Fullsun'), ('partial sun', 'Partsun'), ('partial shade', 'Partshade'), ('full shade', 'Fullshade')], max_length=13, null=True, verbose_name='sun level'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='variety',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='variety'),
        ),
        migrations.AlterField(
            model_name='plants',
            name='water_req',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name='water requirement'),
        ),
        migrations.AlterField(
            model_name='replies',
            name='body',
            field=models.TextField(verbose_name='body'),
        ),
        migrations.AlterField(
            model_name='replies',
            name='forum_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_management.forums'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('Admin', 'Ad'), ('User', 'Us'), ('Moderator', 'Mo')], default='User', max_length=9, verbose_name='role'),
        ),
    ]
