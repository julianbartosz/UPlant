# backend/root/user_management/admin.py

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count
from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm
from allauth.socialaccount.models import SocialAccount

from user_management.models import User


class AdminAuthenticationForm(AuthenticationForm):
    """Admin login form that uses email field instead of username"""
    username = forms.EmailField(label="Email", widget=forms.TextInput(attrs={'autofocus': True}))


admin.site.login_form = AdminAuthenticationForm


class UserCreationForm(forms.ModelForm):
    """Form for creating new users in the admin interface"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username', 'is_active', 'is_superuser')

    def clean_password2(self):
        """Check that the two password entries match"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        """Save the provided password in hashed format"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """Form for updating users in the admin interface"""
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text=("Raw passwords are not stored, so there is no way to see this "
                  "user's password, but you can change the password using "
                  "<a href=\"../password/\">this form</a>.")
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'is_active', 'is_superuser', 
                 'groups', 'user_permissions')

    def clean_password(self):
        # Return the initial value regardless of what the user provides
        return self.initial["password"]


class AccountStatusFilter(SimpleListFilter):
    """Filter for user account status"""
    title = 'Account Status'
    parameter_name = 'account_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('social', 'Social Account'),
            ('verified', 'Email Verified'),
            ('unverified', 'Email Unverified'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)
        if self.value() == 'social':
            return queryset.filter(socialaccount__isnull=False).distinct()
        if self.value() == 'verified':
            return queryset.filter(emailaddress__verified=True).distinct()
        if self.value() == 'unverified':
            return queryset.filter(emailaddress__verified=False).distinct()


class GardenCountFilter(SimpleListFilter):
    """Filter for users based on number of gardens they have"""
    title = 'Garden Count'
    parameter_name = 'garden_count'

    def lookups(self, request, model_admin):
        return (
            ('none', 'No Gardens'),
            ('one', '1 Garden'),
            ('few', '2-5 Gardens'),
            ('many', '6+ Gardens'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.annotate(garden_count=Count('gardens')).filter(garden_count=0)
        if self.value() == 'one':
            return queryset.annotate(garden_count=Count('gardens')).filter(garden_count=1)
        if self.value() == 'few':
            return queryset.annotate(garden_count=Count('gardens')).filter(garden_count__range=(2, 5))
        if self.value() == 'many':
            return queryset.annotate(garden_count=Count('gardens')).filter(garden_count__gte=6)


class SocialAccountInline(admin.TabularInline):
    """Inline admin for social accounts"""
    model = SocialAccount
    extra = 0
    readonly_fields = ('provider', 'uid', 'last_login', 'date_joined')
    fields = ('provider', 'uid', 'last_login', 'date_joined')
    can_delete = False
    max_num = 0  # Don't allow additions
    
    def has_add_permission(self, request, obj=None):
        return False


class UserAdmin(BaseUserAdmin):
    """Enhanced admin interface for User model"""
    form = UserChangeForm
    add_form = UserCreationForm
    
    list_display = ('email', 'username', 'account_status', 'created_at_formatted', 
                   'last_login_formatted', 'social_accounts', 'garden_count')
    
    list_filter = ('is_superuser', 'is_active', AccountStatusFilter, GardenCountFilter, 'created_at')
    
    search_fields = ('email', 'username', 'socialaccount__uid')
    
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'last_login', 'social_accounts_list')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Information', {'fields': ('username', 'zip_code')}),
        ('Account Status', {
            'fields': ('is_active', 'is_superuser'),
            'description': 'Control user access and permissions.'
        }),
        ('Permissions', {'fields': ('groups', 'user_permissions'), 'classes': ('collapse',)}),
        ('Important Dates', {'fields': ('last_login', 'created_at')}),
        ('Social Accounts', {'fields': ('social_accounts_list',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_superuser')
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)
    
    def get_queryset(self, request):
        """Enhance queryset with annotations for performance"""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            garden_count_annotation=Count('gardens', distinct=True),
            social_count=Count('socialaccount', distinct=True)
        )
        return queryset
    
    def garden_count(self, obj):
        """Display garden count with link to filtered garden admin"""
        count = getattr(obj, 'garden_count_annotation', 0)
        if count > 0:
            url = reverse('admin:gardens_garden_changelist') + f'?user__id__exact={obj.id}'
            return format_html('<a href="{}">{} garden{}</a>', url, count, 's' if count > 1 else '')
        return '0'
    garden_count.short_description = 'Gardens'
    garden_count.admin_order_field = 'garden_count_annotation'
    
    def account_status(self, obj):
        """Display account status with color indicator"""
        if not obj.is_active:
            return format_html('<span style="color: red; font-weight: bold;">Inactive</span>')
        
        # Super users get special formatting
        if obj.is_superuser:
            return format_html('<span style="color: purple; font-weight: bold;">Admin</span>')
            
        # Check for email verification status
        try:
            has_verified = obj.emailaddress_set.filter(verified=True).exists()
        except AttributeError:  # If emailaddress_set doesn't exist
            has_verified = True  # Assume verified if not using allauth email verification
        
        if not has_verified:
            return format_html('<span style="color: orange;">Unverified</span>')
        
        return format_html('<span style="color: green;">Active</span>')
    account_status.short_description = 'Status'
    
    def created_at_formatted(self, obj):
        """Format join date for easier reading"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days < 1:
            return format_html('<span style="color: green;">Today</span>')
        elif diff.days < 7:
            return format_html('<span style="color: #3CB371;">{} days ago</span>', diff.days)
        elif diff.days < 30:
            weeks = diff.days // 7
            return format_html('<span>{} week{} ago</span>', weeks, 's' if weeks > 1 else '')
        else:
            return obj.created_at.strftime("%b %d, %Y")
    created_at_formatted.short_description = 'Joined'
    created_at_formatted.admin_order_field = 'created_at'
    
    def last_login_formatted(self, obj):
        """Format last login date with coloring for recent activity"""
        if not obj.last_login:
            return 'Never'
            
        now = timezone.now()
        diff = now - obj.last_login
        
        if diff.days < 1:
            hours = diff.seconds // 3600
            if hours < 1:
                return format_html('<span style="color: green; font-weight: bold;">Just now</span>')
            return format_html('<span style="color: green;">{} hour{} ago</span>', 
                              hours, 's' if hours != 1 else '')
        elif diff.days < 7:
            return format_html('<span style="color: #3CB371;">{} day{} ago</span>', 
                              diff.days, 's' if diff.days != 1 else '')
        elif diff.days < 30:
            return format_html('<span>{} week{} ago</span>', 
                              diff.days // 7, 's' if diff.days // 7 != 1 else '')
        else:
            return obj.last_login.strftime("%b %d, %Y")
    last_login_formatted.short_description = 'Last Login'
    last_login_formatted.admin_order_field = 'last_login'
    
    def social_accounts(self, obj):
        """Display social account indicators"""
        try:
            accounts = obj.socialaccount_set.all()
            if not accounts:
                return ''
                
            providers = [account.provider for account in accounts]
            provider_icons = {
                'google': '🔵',  # Blue circle for Google
            }
            
            icons = [provider_icons.get(provider, '•') for provider in providers]
            return ' '.join(icons)
        except AttributeError:
            return ''
    social_accounts.short_description = 'Social'
    
    def social_accounts_list(self, obj):
        """Display detailed social account information"""
        try:
            accounts = obj.socialaccount_set.all()
            if not accounts:
                return "No connected social accounts"
                
            html = ['<ul>']
            for account in accounts:
                html.append(f'<li><strong>{account.provider.title()}</strong>: {account.uid}</li>')
            html.append('</ul>')
            return format_html(''.join(html))
        except AttributeError:
            return "Social accounts not available"
    social_accounts_list.short_description = "Connected Social Accounts"
    
    # Custom admin actions
    actions = ['activate_users', 'deactivate_users', 'send_verification_email']
    
    def activate_users(self, request, queryset):
        """Bulk activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {updated} users.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate selected users"""
        # Prevent deactivating yourself
        if request.user.id in queryset.values_list('id', flat=True):
            self.message_user(request, "You cannot deactivate yourself!", level='ERROR')
            return
            
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {updated} users.")
    deactivate_users.short_description = "Deactivate selected users"
    
    def send_verification_email(self, request, queryset):
        """Send verification emails to selected users"""
        try:
            from allauth.account.models import EmailAddress
            count = 0
            for user in queryset:
                email_addresses = EmailAddress.objects.filter(user=user, verified=False)
                for email_address in email_addresses:
                    email_address.send_confirmation(request)
                    count += 1
            self.message_user(request, f"Sent {count} verification emails.")
        except ImportError:
            self.message_user(request, "Email verification requires django-allauth.", level='ERROR')
    send_verification_email.short_description = "Send verification emails"
    
    def get_inlines(self, request, obj=None):
        """Add SocialAccount inline only when viewing an existing user"""
        if obj:
            return [SocialAccountInline]
        return []


admin.site.unregister(Group)
admin.site.register(User, UserAdmin)