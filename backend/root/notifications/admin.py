# backend/root/notifications/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count

from notifications.models import (
    Notification, NotificationInstance, NotificationPlantAssociation, NotifTypes
)

class NotificationPlantAssociationInline(admin.TabularInline):
    """Inline admin for plant associations within notifications"""
    model = NotificationPlantAssociation
    extra = 1
    autocomplete_fields = ['plant']
    fields = ('plant', 'custom_interval')

class NotificationInstanceInline(admin.TabularInline):
    """Inline admin for notification instances within notifications"""
    model = NotificationInstance
    extra = 0
    fields = ('next_due', 'status', 'last_completed', 'is_overdue_display')
    readonly_fields = ('is_overdue_display', 'status_display')
    
    def is_overdue_display(self, obj):
        """Display overdue status with visual indicator"""
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold">⚠️ Overdue</span>')
        return format_html('<span style="color: green">On time</span>')
    is_overdue_display.short_description = "Status"
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'PENDING': 'blue',
            'COMPLETED': 'green',
            'SKIPPED': 'orange',
            'CANCELLED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold">{}</span>', color, obj.status)
    status_display.short_description = "Status"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'garden_link', 'plant_count', 'next_due', 'status', 'created_at')
    list_filter = ('type', 'garden__name', 'created_at')
    search_fields = ('name', 'subtype', 'garden__name', 'plants__common_name')
    inlines = [NotificationPlantAssociationInline, NotificationInstanceInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'garden', ('type', 'subtype'))
        }),
        ('Schedule', {
            'fields': ('interval',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def notification_type(self, obj):
        """Display the notification type with subtype if applicable"""
        type_display = obj.get_type_display()
        if obj.type == 'OT' and obj.subtype:
            return f"{type_display} ({obj.subtype})"
        return type_display
    notification_type.short_description = "Type"
    
    def garden_link(self, obj):
        """Make the garden name a clickable link to the garden admin page"""
        if obj.garden:
            link = reverse("admin:gardens_garden_change", args=[obj.garden.id])
            return format_html('<a href="{}">{}</a>', link, obj.garden.name or f"Garden {obj.garden.id}")
        return "—"
    garden_link.short_description = "Garden"
    
    def plant_count(self, obj):
        """Show count of associated plants"""
        count = obj.plants.count()
        return count
    plant_count.short_description = "Plants"
    
    def next_due(self, obj):
        """Show the next due date of the notification"""
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        if instance:
            overdue = instance.is_overdue
            date_str = instance.next_due.strftime("%b %d, %Y %H:%M")
            color = "red" if overdue else "green"
            return format_html('<span style="color: {}; font-weight: {};">{}</span>', 
                              color, "bold" if overdue else "normal", date_str)
        return "—"
    next_due.short_description = "Next Due"
    
    def status(self, obj):
        """Show the current status of the notification"""
        instance = obj.instances.filter(status='PENDING').order_by('next_due').first()
        if not instance:
            # Check if there are any completed instances
            completed = obj.instances.filter(status='COMPLETED').exists()
            if completed:
                return format_html('<span style="color: green;">Completed</span>')
            return "—"
            
        if instance.is_overdue:
            days = (timezone.now() - instance.next_due).days
            return format_html('<span style="color: red; font-weight: bold">Overdue ({} days)</span>', days)
        else:
            # Calculate days until due
            days = (instance.next_due - timezone.now()).days
            return format_html('<span style="color: blue;">Due in {} days</span>', days)
    status.short_description = "Status"
    
    # Add admin actions
    actions = ['mark_completed', 'reset_notifications', 'duplicate_notifications']
    
    def mark_completed(self, request, queryset):
        """Mark all pending instances of selected notifications as completed"""
        count = 0
        for notification in queryset:
            instances = notification.instances.filter(status='PENDING')
            for instance in instances:
                instance.status = 'COMPLETED'
                instance.last_completed = timezone.now()
                instance.save()
                count += 1
        
        self.message_user(request, f"Marked {count} notification instances as completed")
    mark_completed.short_description = "Mark selected notifications as completed"
    
    def reset_notifications(self, request, queryset):
        """Reset notification schedule by clearing instances and creating new ones"""
        for notification in queryset:
            # Delete all instances
            notification.instances.all().delete()
            
            # Create new instance
            NotificationInstance.objects.create(
                notification=notification,
                next_due=timezone.now(),
                status='PENDING'
            )
        
        self.message_user(request, f"Reset {queryset.count()} notification schedules")
    reset_notifications.short_description = "Reset notification schedules"
    
    def duplicate_notifications(self, request, queryset):
        """Duplicate selected notifications"""
        count = 0
        for notification in queryset:
            # Create new notification
            new_notif = Notification.objects.create(
                garden=notification.garden,
                name=f"Copy of {notification.name}",
                type=notification.type,
                subtype=notification.subtype,
                interval=notification.interval
            )
            
            # Copy plant associations
            for assoc in notification.notificationplantassociation_set.all():
                NotificationPlantAssociation.objects.create(
                    notification=new_notif,
                    plant=assoc.plant,
                    custom_interval=assoc.custom_interval
                )
            
            # Create first instance
            NotificationInstance.objects.create(
                notification=new_notif,
                next_due=timezone.now() + timezone.timedelta(days=notification.interval),
                status='PENDING'
            )
            
            count += 1
        
        self.message_user(request, f"Created {count} notification copies")
    duplicate_notifications.short_description = "Duplicate selected notifications"


@admin.register(NotificationInstance)
class NotificationInstanceAdmin(admin.ModelAdmin):
    list_display = ('notification_link', 'notification_type', 'garden_name', 'next_due_colored', 'status_colored', 'last_completed')
    list_filter = ('status', 'notification__type', 'notification__garden__name')
    search_fields = ('notification__name', 'message')
    date_hierarchy = 'next_due'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification', 'next_due')
        }),
        ('Status', {
            'fields': ('status', 'last_completed')
        }),
    )
    
    readonly_fields = ('notification',)
    
    def notification_link(self, obj):
        """Make the notification name a clickable link"""
        link = reverse("admin:notifications_notification_change", args=[obj.notification.id])
        return format_html('<a href="{}">{}</a>', link, obj.notification.name)
    notification_link.short_description = "Notification"
    
    def notification_type(self, obj):
        """Display notification type"""
        type_display = obj.notification.get_type_display()
        if obj.notification.type == 'OT' and obj.notification.subtype:
            return f"{type_display} ({obj.notification.subtype})"
        return type_display
    notification_type.short_description = "Type"
    
    def garden_name(self, obj):
        """Display garden name with link"""
        garden = obj.notification.garden
        link = reverse("admin:gardens_garden_change", args=[garden.id])
        return format_html('<a href="{}">{}</a>', link, garden.name or f"Garden {garden.id}")
    garden_name.short_description = "Garden"
    
    def next_due_colored(self, obj):
        """Display next due date with color coding for overdue"""
        if obj.is_overdue:
            days = (timezone.now() - obj.next_due).days
            return format_html('<span style="color: red; font-weight: bold;">{} (Overdue {} days)</span>', 
                             obj.next_due.strftime("%b %d, %Y"), days)
        else:
            return format_html('<span>{}</span>', obj.next_due.strftime("%b %d, %Y %H:%M"))
    next_due_colored.short_description = "Next Due"
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'PENDING': 'blue',
            'COMPLETED': 'green',
            'SKIPPED': 'orange',
            'CANCELLED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.status)
    status_colored.short_description = "Status"
    
    # Add admin actions
    actions = ['mark_completed', 'mark_skipped', 'reschedule_for_today']
    
    def mark_completed(self, request, queryset):
        """Mark selected instances as completed"""
        count = queryset.update(status='COMPLETED', last_completed=timezone.now())
        self.message_user(request, f"Marked {count} instances as completed")
    mark_completed.short_description = "Mark as completed"
    
    def mark_skipped(self, request, queryset):
        """Mark selected instances as skipped"""
        count = queryset.update(status='SKIPPED')
        self.message_user(request, f"Marked {count} instances as skipped")
    mark_skipped.short_description = "Mark as skipped"
    
    def reschedule_for_today(self, request, queryset):
        """Reschedule selected instances for today"""
        now = timezone.now()
        count = queryset.update(next_due=now, status='PENDING')
        self.message_user(request, f"Rescheduled {count} instances for today")
    reschedule_for_today.short_description = "Reschedule for today"


@admin.register(NotificationPlantAssociation)
class NotificationPlantAssociationAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_name', 'plant_name', 'custom_interval')
    list_filter = ('notification__type', 'notification__garden__name')
    search_fields = ('notification__name', 'plant__common_name', 'plant__scientific_name')
    
    def notification_name(self, obj):
        """Display notification name with link"""
        link = reverse("admin:notifications_notification_change", args=[obj.notification.id])
        return format_html('<a href="{}">{}</a>', link, obj.notification.name)
    notification_name.short_description = "Notification"
    
    def plant_name(self, obj):
        """Display plant name with link"""
        link = reverse("admin:plants_plant_change", args=[obj.plant.id])
        name = obj.plant.common_name or obj.plant.scientific_name or f"Plant {obj.plant.id}"
        return format_html('<a href="{}">{}</a>', link, name)
    plant_name.short_description = "Plant"