from django.db import models
from accounts.models import CustomUser
from matches.models import Match
import uuid

# Create your models here.

class Group(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    match = models.OneToOneField(to=Match, on_delete=models.CASCADE, related_name="group")
    name = models.CharField(blank=False)

    def __str__(self):
        return f"name: {self.name}, users: {self.users}"
    
    @property
    def users(self):
        return list(users["user"] for users in self.match.participations.all().values("user"))
    
    @property
    def last_chat(self):
        if self.chat.exists():
            last_chat = self.chat.latest()  
            data = {
                "username": last_chat.username.pk,
                "message": last_chat.message,
                "createdAt": last_chat.createdAt
            }
            return data
        else:
            return None

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    group_id = models.ForeignKey(to=Group, on_delete=models.CASCADE, related_name='chat')
    username = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE, related_name='chat')
    message = models.TextField(blank=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    replyTo = models.OneToOneField('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='replies')

    class Meta:
        ordering = ["-createdAt"]
        get_latest_by = "createdAt"

    def __str__(self):
        return f"group_id: {self.group_id}, username: {self.username}, message: \"{self.message}\""