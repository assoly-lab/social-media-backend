from django.db import models
from api.models import CustomUser,Post
# Create your models here.

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='notifications_sent')
    target_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="notifications_received",null=True,blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE,null=True,blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)