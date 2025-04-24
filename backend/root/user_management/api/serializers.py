# backend/root/user_management/api/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.exceptions import AuthenticationFailed

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

User = get_user_model()

class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
    
class SocialAccountSerializer(serializers.ModelSerializer):
    """Serializer for user's social accounts"""
    provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialAccount
        fields = ['id', 'provider', 'provider_name', 'uid', 'last_login', 'date_joined']
        read_only_fields = fields
    
    def get_provider_name(self, obj):
        """Get the display name for the provider"""
        providers = {
            'google': 'Google',
        }
        return providers.get(obj.provider, obj.provider.capitalize())


class UserSerializer(serializers.ModelSerializer):
    """Base serializer for user data"""
    garden_count = serializers.SerializerMethodField()
    is_email_verified = serializers.SerializerMethodField()
    social_accounts = SocialAccountSerializer(source='socialaccount_set', many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'zip_code', 'date_joined', 'last_login', 
                 'is_active', 'garden_count', 'is_email_verified', 'social_accounts']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_active', 'is_email_verified']
    
    def get_garden_count(self, obj):
        """Get count of user's gardens"""
        try:
            return obj.gardens.count()
        except AttributeError:
            return 0
    
    def get_is_email_verified(self, obj):
        """Check if user's email is verified (using allauth)"""
        try:
            return EmailAddress.objects.filter(user=obj, verified=True).exists()
        except:
            # If allauth isn't properly set up, assume verified
            return True

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change endpoint"""
    current_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate_current_password(self, value):
        """Validate that the current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value
    
    def validate(self, data):
        """Validate that the new passwords match and meet requirements"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': _("Passwords don't match.")})
        
        try:
            validate_password(data['new_password'], self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that the email exists"""
        user_exists = User.objects.filter(email=value).exists()
        # Even if user doesn't exist, don't tell the client 
        # (to prevent email enumeration attacks)
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset"""
    new_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate that the new passwords match and meet requirements"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': _("Passwords don't match.")})
        
        try:
            validate_password(data['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates"""
    social_accounts = SocialAccountSerializer(source='socialaccount_set', many=True, read_only=True)
    email = serializers.EmailField(read_only=True)  # Email changes require verification
    
    class Meta:
        model = User
        fields = ['username', 'email', 'zip_code', 'social_accounts']
        
    def validate_username(self, value):
        """Validate username is unique and properly formatted"""
        # Skip validation if the username isn't changing
        if self.instance and self.instance.username == value:
            return value
            
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("A user with that username already exists."))
        
        if len(value) < 3:
            raise serializers.ValidationError(_("Username must be at least 3 characters long."))
            
        return value


class EmailChangeRequestSerializer(serializers.Serializer):
    """Serializer for requesting an email change"""
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate_new_email(self, value):
        """Validate new email is unique and properly formatted"""
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError(_("Enter a valid email address."))
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("A user with that email already exists."))
            
        # Don't allow changing to the same email
        if self.context['request'].user.email == value:
            raise serializers.ValidationError(_("New email must be different from current email."))
            
        return value
    
    def validate_password(self, value):
        """Validate that the password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Password is incorrect."))
        return value


class AdminUserSerializer(UserSerializer):
    """Extended serializer for admin users to manage other users"""
    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ['is_superuser']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_email_verified']
    
    def update(self, instance, validated_data):
        """Only allow admin users to update user status"""
        request = self.context.get('request')
        if not request or not request.user.is_superuser:
            # Remove admin-only fields for non-admin users
            validated_data.pop('is_active', None)
            validated_data.pop('is_superuser', None)
            
        return super().update(instance, validated_data)


class DisconnectSocialAccountSerializer(serializers.Serializer):
    """Serializer for disconnecting a social account"""
    account_id = serializers.IntegerField(required=True)
    
    def validate_account_id(self, value):
        """Validate that the account exists and belongs to the user"""
        user = self.context['request'].user
        
        try:
            account = SocialAccount.objects.get(id=value, user=user)
            return value
        except SocialAccount.DoesNotExist:
            raise serializers.ValidationError(_("Social account not found or doesn't belong to you."))