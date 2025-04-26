# backend/root/notifications/api/tests/test_api.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from plants.models import Plant
from gardens.models import Garden
from notifications.models import Notification, NotificationInstance, NotificationPlantAssociation, NotifTypes

User = get_user_model()

class NotificationAPITest(APITestCase):
    """Tests for the Notification API endpoints"""
    
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
        
        # Create a garden for the user
        self.garden = Garden.objects.create(
            user=self.user,
            name="Test Garden",
            size_x=5,
            size_y=5
        )
        
        # Create a test plant
        self.plant = Plant.objects.create(
            common_name="Test Plant",
            scientific_name="Testus plantus",
            is_user_created=False
        )
        
        # Create test notifications
        self.notification = Notification.objects.create(
            garden=self.garden,
            name="Test Notification",
            type=NotifTypes.FE,
            interval=7
        )
        
        # Associate the plant with the notification
        self.plant_assoc = NotificationPlantAssociation.objects.create(
            notification=self.notification,
            plant=self.plant
        )
        
        # Create notification instances
        self.notification_instance = NotificationInstance.objects.create(
            notification=self.notification,
            next_due=timezone.now() + timedelta(days=2),
            status='PENDING'
        )
        
        self.overdue_instance = NotificationInstance.objects.create(
            notification=self.notification,
            next_due=timezone.now() - timedelta(days=2),
            status='PENDING'
        )
    
    def test_list_notifications(self):
        """Test listing notifications"""
        url = reverse('notifications_api:notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Notification")
        
    def test_create_notification(self):
        """Test creating a new notification"""
        url = reverse('notifications_api:notification-list')
        data = {
            'garden': self.garden.id,
            'name': "New Notification",
            'type': NotifTypes.PR,
            'interval': 14
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "New Notification")
        self.assertEqual(response.data['type'], NotifTypes.PR)
        
    def test_dashboard_endpoint(self):
        """Test the dashboard endpoint"""
        url = reverse('notifications_api:notification-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overdue', response.data)
        self.assertIn('today', response.data)
        self.assertIn('tomorrow', response.data)
        self.assertIn('this_week', response.data)
        self.assertIn('later', response.data)
        
        # Our overdue instance should be in the 'overdue' list
        self.assertEqual(len(response.data['overdue']), 1)
        
    def test_complete_notification(self):
        """Test completing a notification instance"""
        url = reverse('notifications_api:notification-instance-complete', 
                     args=[self.notification_instance.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check the instance status is now completed
        self.notification_instance.refresh_from_db()
        self.assertEqual(self.notification_instance.status, 'COMPLETED')
    
    def test_skip_notification(self):
        """Test skipping a notification instance"""
        url = reverse('notifications_api:notification-instance-skip', 
                     args=[self.notification_instance.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check the instance status is now skipped
        self.notification_instance.refresh_from_db()
        self.assertEqual(self.notification_instance.status, 'SKIPPED')
    
    def test_upcoming_notifications(self):
        """Test getting upcoming notifications"""
        url = reverse('notifications_api:notification-instance-upcoming')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Both instances should be in the results since both are within 7 days
        self.assertEqual(len(response.data), 2)
        
        # Test with custom days parameter
        url = f"{url}?days=1"
        response = self.client.get(url)
        
        # Only the overdue instance should be included (since it's < 1 day away)
        self.assertEqual(len(response.data), 1)
        
    def test_add_plant_to_notification(self):
        """Test adding a plant to a notification"""
        # Create another test plant
        plant2 = Plant.objects.create(
            common_name="Another Plant",
            scientific_name="Testus secundus",
            is_user_created=False
        )
        
        url = reverse('notifications_api:notification-add-plant', 
                     args=[self.notification.id])
        response = self.client.post(url, {'plant_id': plant2.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check the plant was added
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.plants.count(), 2)