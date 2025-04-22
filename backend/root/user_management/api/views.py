# backend/root/user_management/api/views.py

from django.contrib.auth import get_user_model, login, logout, authenticate
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import viewsets, generics, status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.views import ObtainAuthToken

from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.socialaccount.models import SocialAccount
from allauth.account.utils import send_email_confirmation

from user_management.api.serializers import (
    UserSerializer, PasswordChangeSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, UserProfileSerializer, EmailChangeRequestSerializer,
    AdminUserSerializer, DisconnectSocialAccountSerializer
)
from user_management.api.permissions import IsUserOrAdmin, IsAdminOrReadOnly

User = get_user_model()

class CustomAuthTokenSerializerLocal(serializers.Serializer):
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

from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication that skips CSRF verification entirely
    """
    def enforce_csrf(self, request):
        # Skip CSRF check for API endpoints
        return
    
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(ObtainAuthToken):
    """
    API endpoint for obtaining an authentication token.
    
    POST with email and password to get a token.
    """
    serializer_class = CustomAuthTokenSerializerLocal
    authentication_classes = (CsrfExemptSessionAuthentication,)
    parser_classes = (JSONParser,)
    
    def post(self, request, *args, **kwargs):
        print("Request method:", request.method)
        print("Content type:", request.content_type)
        print("Raw body:", request.body.decode('utf-8'))
        
        data = request.data
        email = data.get('email')
        password = data.get('password')
        
        print(f"Attempting login with: {email}")
        
        try:
            user = User.objects.get(email=email)
            print(f"Found user: {user.username}")
            
            # Try direct authentication
            if user.check_password(password):
                print("Password check passed!")
                # Manual authentication success
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.pk,
                    'email': user.email
                })
            else:
                print("Password check failed!")
                return Response(
                    {'non_field_errors': ['Unable to log in with provided credentials.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            print(f"No user found with email: {email}")
            return Response(
                {'non_field_errors': ['Unable to log in with provided credentials.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"Login exception: {str(e)}")
            return Response(
                {'detail': 'Authentication error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class UserDetailView(generics.RetrieveAPIView):
    """
    Get details of the current user.
    
    Returns profile information for the authenticated user.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View and update user profile.
    
    GET: Retrieve the user's profile information
    PATCH: Update the user's profile information
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(generics.GenericAPIView):
    """
    Change user password.
    
    Requires current password and new password with confirmation.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Change the password
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Update token (optional - force re-login)
            try:
                request.user.auth_token.delete()
            except (AttributeError, ObjectDoesNotExist):
                pass
                
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'detail': _('Password updated successfully.'),
                'token': token.key
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request a password reset.
    
    Sends a password reset email if the email exists in the system.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
                
                # Send password reset email
                from django.core.mail import send_mail
                from django.contrib.auth.tokens import PasswordResetTokenGenerator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                
                token_generator = PasswordResetTokenGenerator()
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = token_generator.make_token(user)
                
                # Build reset URL (frontend should handle this)
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
                
                send_mail(
                    subject="Password Reset Request",
                    message=f"Please use the following link to reset your password: {reset_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except User.DoesNotExist:
                # Don't reveal if email exists or not
                pass
                
            # Always return success to prevent email enumeration
            return Response({'detail': _('Password reset email has been sent if the email exists in our system.')})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm password reset.
    
    Validate token and set new password for the user.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                # Decode the user ID
                uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
                user = User.objects.get(pk=uid)
                
                # Check token validity
                if not default_token_generator.check_token(user, serializer.validated_data['token']):
                    return Response(
                        {'detail': _('Invalid or expired token.')},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Set new password
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                return Response({'detail': _('Password has been reset successfully.')})
            
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {'detail': _('Invalid reset link.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    Verify email address.
    
    Confirms user's email address using token from email.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, key):
        try:
            # Find the email confirmation
            confirmation = EmailConfirmation.objects.get(key=key)
            
            # Confirm the email
            email_address = confirmation.confirm(request)
            
            # If successful, return success response
            if email_address:
                return Response({'detail': _('Email address has been verified.')})
            else:
                return Response(
                    {'detail': _('Email verification failed.')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except EmailConfirmation.DoesNotExist:
            return Response(
                {'detail': _('Invalid verification key.')},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(APIView):
    """
    Resend verification email.
    
    Sends a new verification email to the user's unverified email.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check if user has an unverified email
            email_address = EmailAddress.objects.get(user=request.user, verified=False)
            
            # Send verification email
            send_email_confirmation(request, request.user, email=email_address.email)
            
            return Response({'detail': _('Verification email sent.')})
        except EmailAddress.DoesNotExist:
            # User doesn't have an unverified email
            return Response(
                {'detail': _('No unverified email address found.')},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailChangeRequestView(generics.GenericAPIView):
    """
    Request email change.
    
    Initiates the email change process, sending verification to new email.
    """
    serializer_class = EmailChangeRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_email = serializer.validated_data['new_email']
            
            # Add the new email as a secondary email
            try:
                email_address = EmailAddress.objects.create(
                    user=request.user,
                    email=new_email,
                    primary=False,
                    verified=False
                )
                
                # Send verification email
                send_email_confirmation(request, request.user, email=new_email)
                
                return Response({'detail': _('Verification email sent to new address.')})
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetPrimaryEmailView(APIView):
    """
    Set primary email.
    
    Changes the user's primary email to one of their verified emails.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'detail': _('Email is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Check that this email belongs to the user and is verified
            email_address = EmailAddress.objects.get(
                user=request.user,
                email=email,
                verified=True
            )
            
            # Set as primary
            EmailAddress.objects.filter(user=request.user, primary=True).update(primary=False)
            email_address.primary = True
            email_address.save()
            
            # Update user's email field
            request.user.email = email
            request.user.save()
            
            return Response({'detail': _('Primary email updated.')})
            
        except EmailAddress.DoesNotExist:
            return Response(
                {'detail': _('Email not found or not verified.')},
                status=status.HTTP_400_BAD_REQUEST
            )


class SocialAccountDisconnectView(generics.GenericAPIView):
    """
    Disconnect social account.
    
    Removes connection between user and a social authentication provider.
    """
    serializer_class = DisconnectSocialAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            account_id = serializer.validated_data['account_id']
            
            try:
                # Get the social account
                account = SocialAccount.objects.get(id=account_id, user=request.user)
                
                # Don't allow removal if it's the only way to login
                has_password = request.user.has_usable_password()
                has_other_socials = SocialAccount.objects.filter(user=request.user).count() > 1
                
                if not has_password and not has_other_socials:
                    return Response(
                        {'detail': _('Cannot disconnect the only login method. Please set a password first.')},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Delete the account
                provider = account.provider
                account.delete()
                
                return Response({'detail': f'Successfully disconnected {provider} account.'})
                
            except SocialAccount.DoesNotExist:
                return Response(
                    {'detail': _('Social account not found.')},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only user management.
    
    Full CRUD operations for user management, restricted to admin users.
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Optionally filter users"""
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter by active status
        is_active = self.request.query_params.get('active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        # Filter by email verification
        is_verified = self.request.query_params.get('verified')
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            # Complex filter across a relationship
            if is_verified:
                queryset = queryset.filter(emailaddress__verified=True).distinct()
            else:
                # Users with no verified emails
                verified_users = User.objects.filter(emailaddress__verified=True).distinct()
                queryset = queryset.exclude(id__in=verified_users.values('id'))
                
        # Search by email or username
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) | 
                models.Q(username__icontains=search)
            )
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'detail': _('User activated.')})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account"""
        user = self.get_object()
        
        # Prevent deactivating self
        if user == request.user:
            return Response(
                {'detail': _('You cannot deactivate your own account.')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.is_active = False
        user.save()
        return Response({'detail': _('User deactivated.')})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset a user's password to a random string and email it"""
        user = self.get_object()
        
        # Generate random password
        import random
        import string
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Set password
        user.set_password(password)
        user.save()
        
        # Email the password to the user
        try:
            from django.core.mail import send_mail
            
            send_mail(
                subject="Your password has been reset",
                message=f"Your password has been reset by an administrator. Your new password is: {password}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            return Response({'detail': _('Password reset and email sent.')})
        except Exception as e:
            return Response(
                {'detail': f'Password reset but email failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )