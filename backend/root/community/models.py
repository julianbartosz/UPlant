# backend/root/community/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import UniqueConstraint


class Forums(models.Model):
    user_id = models.ForeignKey('user_management.User', on_delete=models.DO_NOTHING)
    title = models.CharField(_('title'), max_length=50)
    body = models.TextField(_('body'))  # don't allow blank
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('forum')
        verbose_name_plural = _('forums')

    def __str__(self):
        return f"Forum ID:{self.id}"


class Replies(models.Model):
    user_id = models.ForeignKey('user_management.User', on_delete=models.DO_NOTHING)
    forum_id = models.ForeignKey(Forums, on_delete=models.CASCADE)
    parent_id = models.ForeignKey("self", blank=True, null=True, on_delete=models.DO_NOTHING)
    # Note: if parent_id is null, its parent is the initial forum post indicated by forum_id
    body = models.TextField(_('body'))
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('reply')
        verbose_name_plural = _('replies')

    def __str__(self):
        return f"Reply ID:{self.id}"


class Likes(models.Model):
    user_id = models.ForeignKey('user_management.User', on_delete=models.DO_NOTHING)
    reply_id = models.ForeignKey(Replies, on_delete=models.CASCADE)
    ld_value = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        constraints = [
            UniqueConstraint(
                fields=['user_id', 'reply_id'],
                name='unq_vote'
            )
        ]

    def __str__(self):
        return f"Like ID:{self.id}"