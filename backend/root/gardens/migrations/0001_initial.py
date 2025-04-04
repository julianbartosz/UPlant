# Generated by Django 5.0.4 on 2025-03-31 18:18

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('plants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Garden',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=25, null=True, verbose_name='Garden Name')),
                ('size_x', models.PositiveIntegerField(help_text='Length of the garden (e.g., in inches)', verbose_name='Garden Length')),
                ('size_y', models.PositiveIntegerField(help_text='Width of the garden (e.g., in inches)', verbose_name='Garden Width')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when the garden was created')),
                ('is_deleted', models.BooleanField(default=False, help_text='Flag indicating if the garden is deleted (soft delete)')),
                ('user', models.ForeignKey(help_text='Owner of the garden', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'garden',
                'verbose_name_plural': 'gardens',
            },
        ),
        migrations.CreateModel(
            name='GardenLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('planted_date', models.DateField(default=django.utils.timezone.now, help_text='The date when the plant was planted', verbose_name='Date Planted')),
                ('x_coordinate', models.PositiveIntegerField(help_text='X coordinate position in the garden grid', verbose_name='X Coordinate')),
                ('y_coordinate', models.PositiveIntegerField(help_text='Y coordinate position in the garden grid', verbose_name='Y Coordinate')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp when this log was last updated')),
                ('garden', models.ForeignKey(help_text='The garden to which this log belongs', on_delete=django.db.models.deletion.CASCADE, to='gardens.garden')),
                ('plant', models.ForeignKey(blank=True, help_text='The plant placed in the garden', null=True, on_delete=django.db.models.deletion.SET_NULL, to='plants.plant')),
            ],
            options={
                'verbose_name': 'garden log',
                'verbose_name_plural': 'garden logs',
                'ordering': ['garden', 'planted_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='garden',
            constraint=models.CheckConstraint(check=models.Q(('size_x__gt', 0)), name='gardens_check_size_x_pos'),
        ),
        migrations.AddConstraint(
            model_name='garden',
            constraint=models.CheckConstraint(check=models.Q(('size_y__gt', 0)), name='gardens_check_size_y_pos'),
        ),
        migrations.AddConstraint(
            model_name='gardenlog',
            constraint=models.UniqueConstraint(fields=('garden', 'x_coordinate', 'y_coordinate'), name='unique_plot_space'),
        ),
    ]
