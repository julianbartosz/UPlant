from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('gardens', '0002_remove_garden_gardens_check_size_x_pos_and_more'),
    ]

    operations = [
        # Update Garden model Meta options
        migrations.AlterModelOptions(
            name='garden',
            options={'ordering': ['-updated_at'], 'verbose_name': 'garden', 'verbose_name_plural': 'gardens'},
        ),
        
        # Add new fields to Garden model
        migrations.AddField(
            model_name='garden',
            name='description',
            field=models.TextField(blank=True, help_text='Description or notes about this garden', null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='garden',
            name='garden_type',
            field=models.CharField(blank=True, help_text="Type of garden (e.g., 'Vegetable', 'Herb', 'Flower')", max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='garden',
            name='is_public',
            field=models.BooleanField(default=False, help_text='Whether this garden is visible to other users'),
        ),
        migrations.AddField(
            model_name='garden',
            name='location',
            field=models.CharField(blank=True, help_text="General location of the garden (e.g., 'Backyard', 'Balcony')", max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='garden',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Timestamp when the garden was last updated'),
        ),
        
        # Add new fields to GardenLog model
        migrations.AddField(
            model_name='gardenlog',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='Timestamp when this log was created'),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='growth_stage',
            field=models.CharField(blank=True, help_text='Current growth stage of the plant', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='health_status',
            field=models.CharField(default='Healthy', help_text='Current health status of the plant', max_length=15),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='last_fertilized',
            field=models.DateTimeField(blank=True, help_text='When the plant was last fertilized', null=True),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='last_pruned',
            field=models.DateTimeField(blank=True, help_text='When the plant was last pruned', null=True),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='last_watered',
            field=models.DateTimeField(blank=True, help_text='When the plant was last watered', null=True),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='notes',
            field=models.TextField(blank=True, help_text='Additional notes about this plant in the garden', null=True, verbose_name='Notes'),
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='x_position',
            field=models.PositiveIntegerField(default=0, help_text='X position in the garden grid (0-based)', verbose_name='X Position'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gardenlog',
            name='y_position',
            field=models.PositiveIntegerField(default=0, help_text='Y position in the garden grid (0-based)', verbose_name='Y Position'),
            preserve_default=False,
        ),
        
        # Update model fields if needed
        migrations.AlterField(
            model_name='garden',
            name='is_deleted',
            field=models.BooleanField(default=False, help_text='Flag for soft deletion'),
        ),
        migrations.AlterField(
            model_name='garden',
            name='name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Garden Name'),
        ),
        migrations.AlterField(
            model_name='garden',
            name='user',
            field=models.ForeignKey(help_text='Owner of the garden', on_delete=django.db.models.deletion.CASCADE, related_name='gardens', to='user_management.user'),
        ),
        
        # Use unique_together instead of constraint
        migrations.AlterUniqueTogether(
            name='gardenlog',
            unique_together={('garden', 'x_position', 'y_position')},
        ),
    ]