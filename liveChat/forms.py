from django import forms
from .models import Group, Chat

try:
    from typing import override  
except ImportError:
    def override(func): 
        return func


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["match", "name"]


class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ["group_id", "username", "message", "replyTo"]
