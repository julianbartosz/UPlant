# Generated by Django 5.0.4 on 2025-03-03 23:06

import datetime
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plants',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('species', models.CharField(max_length=50)),
                ('variety', models.CharField(blank=True, max_length=50, null=True)),
                ('maturity_time', models.PositiveIntegerField()),
                ('is_deleted', models.BooleanField(default=False)),
                ('germination_time', models.PositiveIntegerField(blank=True, null=True)),
                ('spacing_x', models.PositiveIntegerField(blank=True, null=True)),
                ('spacing_y', models.PositiveIntegerField(blank=True, null=True)),
                ('sun_level', models.CharField(blank=True, choices=[('full sun', 'Fullsun'), ('partial sun', 'Partsun'), ('partial shade', 'Partshade'), ('full shade', 'Fullshade')], max_length=13, null=True)),
                ('planting_depth', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('water_req', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('plant_description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Replies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('username', models.CharField(max_length=50, unique=True, verbose_name='username')),
                ('role', models.CharField(choices=[('admin', 'Ad'), ('user', 'Us'), ('moderator', 'Mo')], default='user', max_length=9, verbose_name='role')),
                ('zip_code', models.CharField(blank=True, max_length=5, null=True, validators=[django.core.validators.MinLengthValidator(5)], verbose_name='zip code')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
    ]
