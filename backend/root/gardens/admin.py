# backend/root/gardens/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from gardens.models import Garden, GardenLog, PlantHealthStatus

class GardenLogInline(admin.TabularInline):
    """Display garden logs inline within Garden detail view"""
    model = GardenLog
    extra = 0
    
    fields = ('plant', 'x_coordinate', 'y_coordinate', 'planted_date', 'health_status', 'last_watered')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['x_coordinate'].initial = 0
        formset.form.base_fields['y_coordinate'].initial = 0
        return formset
    
    # custom position_display method
    def position_display(self, obj):
        """Format position as (x, y)"""
        return f"({obj.x_coordinate}, {obj.y_coordinate})"
    position_display.short_description = "Position"
    
    autocomplete_fields = ['plant']
    

@admin.register(Garden)
class GardenAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'size_display', 'plant_count', 'created_at', 'is_active')
    list_filter = ('is_public', 'is_deleted', 'garden_type', 'created_at')
    search_fields = ('name', 'user__username', 'location')
    date_hierarchy = 'created_at'
    
    inlines = [GardenLogInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'description')
        }),
        ('Dimensions', {
            'fields': (('size_x', 'size_y'),)
        }),
        ('Settings', {
            'fields': ('garden_type', 'location', 'is_public', 'is_deleted')
        }),
    )
    
    def size_display(self, obj):
        """Display garden size as WxH"""
        return f"{obj.size_x} × {obj.size_y}"
    size_display.short_description = "Size"
    
    def is_active(self, obj):
        """Show a green/red indicator for active gardens"""
        if not obj.is_deleted:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    is_active.short_description = "Active"
    
    def plant_count(self, obj):
        """Show count of plants in the garden"""
        return obj.logs.count()
    plant_count.short_description = "Plants"
    
    # Add admin actions
    actions = ['mark_as_deleted', 'mark_as_active', 'make_public', 'make_private']
    
    def mark_as_deleted(self, request, queryset):
        """Mark selected gardens as deleted"""
        queryset.update(is_deleted=True)
    mark_as_deleted.short_description = "Mark selected gardens as deleted"
    
    def mark_as_active(self, request, queryset):
        """Mark selected gardens as active"""
        queryset.update(is_deleted=False)
    mark_as_active.short_description = "Mark selected gardens as active"
    
    def make_public(self, request, queryset):
        """Make selected gardens public"""
        queryset.update(is_public=True)
    make_public.short_description = "Make selected gardens public"
    
    def make_private(self, request, queryset):
        """Make selected gardens private"""
        queryset.update(is_public=False)
    make_private.short_description = "Make selected gardens private"
    
    def get_queryset(self, request):
        """Include counts in queryset for better performance"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            plant_count=Count('logs')
        )
        return queryset


@admin.register(GardenLog)
class GardenLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'plant_name', 'garden_name', 'position', 'health_status_colored', 'planted_date')
    list_filter = ('health_status', 'planted_date', 'garden__name')
    search_fields = ('plant__common_name', 'plant__scientific_name', 'notes', 'garden__name')
    date_hierarchy = 'planted_date'
    
    autocomplete_fields = ['garden', 'plant']
    
    fieldsets = (
        ('Garden & Plant', {
            'fields': ('garden', 'plant')
        }),
        ('Position & Date', {
            'fields': (('x_coordinate', 'y_coordinate'), 'planted_date')
        }),
        ('Health & Status', {
            'fields': ('health_status', 'notes')
        }),
        ('Care History', {
            'fields': ('last_watered', 'last_fertilized', 'last_pruned', 'growth_stage'),
            'classes': ('collapse',)
        }),
    )
    
    def plant_name(self, obj):
        """Display plant name with scientific name as title"""
        if not obj.plant:
            return "—"
        return format_html(
            '<span title="{}">{}</span>', 
            obj.plant.scientific_name or "Unknown",
            obj.plant.common_name or obj.plant.scientific_name or "Unknown Plant"
        )
    plant_name.short_description = "Plant"
    
    def garden_name(self, obj):
        """Display garden name"""
        return obj.garden.name or f"Garden {obj.garden.id}"
    garden_name.short_description = "Garden"
    
    def position(self, obj):
        """Format position as (x, y)"""
        return f"({obj.x_coordinate}, {obj.y_coordinate})"
    position.short_description = "Position"
    
    def health_status_colored(self, obj):
        """Display health status with color indicator"""
        colors = {
            PlantHealthStatus.EXCELLENT: "darkgreen",
            PlantHealthStatus.HEALTHY: "green",
            PlantHealthStatus.FAIR: "#9ACD32",  # Yellow-green
            PlantHealthStatus.POOR: "orange",
            PlantHealthStatus.DYING: "red",
            PlantHealthStatus.DEAD: "grey",
            PlantHealthStatus.UNKNOWN: "#CCCCCC",
        }
        color = colors.get(obj.health_status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold">{}</span>', 
            color, 
            obj.get_health_status_display()
        )
    health_status_colored.short_description = "Health"
    
    actions = ['mark_as_healthy', 'mark_as_watered', 'mark_as_fertilized', 'mark_as_pruned']
    
    def mark_as_healthy(self, request, queryset):
        """Mark selected plants as healthy"""
        queryset.update(health_status=PlantHealthStatus.HEALTHY)
    mark_as_healthy.short_description = "Mark selected plants as healthy"
    
    def mark_as_watered(self, request, queryset):
        """Mark selected plants as watered now"""
        for log in queryset:
            log.record_watering()
    mark_as_watered.short_description = "Mark selected plants as watered now"
    
    def mark_as_fertilized(self, request, queryset):
        """Mark selected plants as fertilized now"""
        for log in queryset:
            log.record_fertilizing()
    mark_as_fertilized.short_description = "Mark selected plants as fertilized now"
    
    def mark_as_pruned(self, request, queryset):
        """Mark selected plants as pruned now"""
        for log in queryset:
            log.record_pruning()
    mark_as_pruned.short_description = "Mark selected plants as pruned now"