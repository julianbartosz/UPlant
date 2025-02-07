class Notification:
    """
    Notification holds the information necessary to notify a user.

    Notifying a user requires at least one notification handler to be
    registered by overriding `handlers`.
    """
    handlers = ()

    def __init__(self, user, **kwargs):
        self.user = user
        for key, value in kwargs.items():
            setattr(self, key, value)

    def notify(self):
        """Use all registered handlers to notify the user."""
        for handler in self.handlers:
            handler(self)
