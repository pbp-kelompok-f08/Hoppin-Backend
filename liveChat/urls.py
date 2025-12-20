from django.urls import path
from .views import *

app_name = 'liveChat'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('chat/<uuid:group_id>/', operate_chat_by_group, name='operate_chat_by_group'),
    path('chat/none/<uuid:chat_id>/', operate_chat_by_group, name='operate_chat_by_group'),
    path('chat/update/<uuid:chat_id>/', operate_chat_by_group_patch, name='update_chat'),
    path('chat/delete/<uuid:chat_id>/', operate_chat_by_group_delete, name='update_chat'),
    path('chat/delete/all/<uuid:group_id>/', operate_chat_by_group_delete, name='update_chat'),
    path('group/', operate_group, name='operate_group'),
    path('group/<uuid:group_id>/', operate_group, name= 'operate_group'),
]
