# backend/root/community/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

# Custom Manager for non-deleted info
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Forum(models.Model):
    user = models.ForeignKey(
        'user_management.User', 
        on_delete=models.DO_NOTHING, 
        help_text="User who created the forum"
    )
    title = models.CharField(_('Title'), max_length=50)
    body = models.TextField(_('Body'))
    view_count = models.PositiveIntegerField(default=0, help_text="Number of times the forum has been viewed")
    is_approved = models.BooleanField(default=False, help_text="Indicates if the forum has been approved by a moderator")
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Moderator who approved this forum", related_name="approved_forums"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the forum was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the forum was last updated")
    is_deleted = models.BooleanField(default=False, help_text="Flag indicating if the forum is deleted")
    
    objects = ActiveManager()  # Default manager returns only non-deleted forums
    all_objects = models.Manager()  # Includes all records, even deleted ones

    class Meta:
        verbose_name = _('forum')
        verbose_name_plural = _('forums')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Forum {self.id} - {self.title}"
    
    def top_level_replies(self):
        """Return replies that do not have a parent (top-level replies)."""
        return self.reply_set.filter(parent__isnull=True, is_deleted=False)
    
    def increment_view_count(self):
        """Increment the view count by one."""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])


class Reply(models.Model):
    user = models.ForeignKey(
        'user_management.User', 
        on_delete=models.DO_NOTHING, 
        help_text="User who posted the reply"
    )
    forum = models.ForeignKey(
        Forum, 
        on_delete=models.CASCADE, 
        help_text="Forum to which this reply belongs"
    )
    parent = models.ForeignKey(
        "self", 
        blank=True, 
        null=True, 
        on_delete=models.DO_NOTHING, 
        help_text="Parent reply for threaded discussions"
    )
    body = models.TextField(_('Body'))
    is_approved = models.BooleanField(default=False, help_text="Indicates if the reply has been approved by a moderator")
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Moderator who approved this reply", related_name="approved_replies"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the reply was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the reply was last updated")
    is_deleted = models.BooleanField(default=False, help_text="Flag indicating if the reply is deleted")
    
    objects = ActiveManager()  # Default manager returns only non-deleted replies
    all_objects = models.Manager()  # Includes all replies

    class Meta:
        verbose_name = _('reply')
        verbose_name_plural = _('replies')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['forum']),
        ]
    
    def __str__(self):
        return f"Reply {self.id} by {self.user}"
    
    def children(self):
        """Return all direct child replies that are not deleted."""
        return Reply.objects.filter(parent=self, is_deleted=False)
    
    def get_all_children(self):
        """Recursively retrieve all nested child replies."""
        all_children = list(self.children())
        for child in self.children():
            all_children.extend(child.get_all_children())
        return all_children

    @property
    def is_edited(self):
        """Return True if the reply has been updated after creation."""
        return self.updated_at > self.created_at
    
    @property
    def like_count(self):
        """Return the total number of likes for this reply."""
        return self.like_set.count()


class Like(models.Model):
    user = models.ForeignKey(
        'user_management.User', 
        on_delete=models.DO_NOTHING, 
        help_text="User who liked the reply"
    )
    reply = models.ForeignKey(
        Reply, 
        on_delete=models.CASCADE, 
        help_text="Reply that was liked"
    )
    ld_value = models.BooleanField(default=False, help_text="Boolean value for like/dislike, if applicable")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the like was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the like was last updated")
    
    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        constraints = [
            UniqueConstraint(fields=['user', 'reply'], name='unique_like')
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Like {self.id} by {self.user}"
