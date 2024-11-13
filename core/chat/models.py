from django.db import models
from api.models import CustomUser

# Create your models here.

class ChatMessage(models.Model):
    sender = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"