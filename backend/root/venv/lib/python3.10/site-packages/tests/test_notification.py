from unittest import TestCase
from unittest.mock import MagicMock

from pigeon.notification import Notification


class TestNotification(TestCase):
    """Test the Notification class."""

    def setUp(self):
        self.pigeon_handler = MagicMock()
        self.user = 'Test User'

    def test_notify(self):
        """The notification uses each registered handler to notify a user."""
        class CustomNotification(Notification):
            handlers = (self.pigeon_handler,)

        notification = CustomNotification(user=self.user)
        notification.notify()

        self.pigeon_handler.assert_called_once_with(notification)

    def test_init(self):
        """A notification stores information for the handlers to access."""
        template = 'test_template.txt'
        notification = Notification(user=self.user, template=template)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.template, template)
