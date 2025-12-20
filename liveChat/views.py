from django.shortcuts import render, get_object_or_404
from .models import Group, Chat
from django.core import serializers
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from accounts.models import CustomUser
from .forms import *
import uuid
import json

# Create your views here.
@login_required
def show_main(request: HttpRequest):
    print("anjay")
    group = Group.objects.all()
    data = serializers.serialize("json", group)
    return JsonResponse({"data": json.loads(data)}, status=200)

@login_required
@csrf_exempt
def operate_group(request: HttpRequest, group_id: uuid = ''):
    print("fetch here!")
    match request.method:
        case "GET":
            return operate_group_get(request, group_id)
        case "PATCH":
            return operate_group_patch(request, group_id)
        case "DELETE":
            return operate_group_delete(request.user, group_id)
        case _:
            return HttpResponse(status=405)

def operate_group_get(request: HttpRequest, group_id: uuid):
    user = request.user
    search_name = request.GET.get("group_name", "").lower()
    if user.role != 'admin' and group_id:
        print("disini nuh")
        group = get_object_or_404(Group, id=group_id)
        data = model_to_dict(group)
        data["members"] = group.users
        return JsonResponse({"data": data}, status=200)
    elif user.role != 'admin' and search_name:
        print("disini nah")
        user_participations = user.participations.all()
        data = []
        for user_participation in user_participations:
            match = user_participation.match
            group = match.group
            if group.name.lower().count(search_name):
                group_dict = model_to_dict(group)
                group_dict["members"] = group.users
                group_dict["last_chat"] = group.last_chat
                print(group_dict)
                data.append(group_dict)
        return JsonResponse({"data": data}, status=200)
    elif user.role != 'admin':
        print("disini noh")
        user_participations = user.participations.all()
        data = []
        for user_participation in user_participations:
            match = user_participation.match
            group = match.group
            group_dict = model_to_dict(group)
            group_dict["members"] = group.users
            group_dict["last_chat"] = group.last_chat
            print(group_dict)
            data.append(group_dict)
        return JsonResponse({"data": data}, status=200)
    elif group_id:
        print("disini neh")
        group = get_object_or_404(Group, id=group_id)
        data = model_to_dict(group)
        data["members"] = group.users
        return JsonResponse({"data": data}, status=200)
    else:
        print("disini nih")
        group = Group.objects.all()
        data = serializers.serialize("json", group)
        return JsonResponse({"data": json.loads(data)}, status=200)

def operate_group_patch(request: HttpRequest, group_id: uuid):
    data = json.loads(request.body)
    group = get_object_or_404(Group, id=group_id)
    if (data['name']):
        group.name = data['name']
    group.save()
    return HttpResponse(status=204)

def operate_group_delete(user: CustomUser, group_id: uuid = ''):
    if (user.role != 'admin'):
        return HttpResponse(status=401)
    elif (group_id):
        Group.objects.get(id=group_id).delete()
    else:
        Group.objects.all().delete()
    return HttpResponse(status=204)

@login_required
@csrf_exempt
def operate_chat_by_group(request: HttpRequest, group_id: uuid = None, chat_id: uuid = None):
    print("here 2")
    match request.method:
        case "GET":
            return operate_chat_by_group_get(request.user, group_id)
        case "POST":
            return operate_chat_by_group_post(request, group_id)
        case "DELETE":
            return operate_chat_by_group_delete(request, group_id, chat_id)
        case _: 
            return HttpResponse(status=405)

def operate_chat_by_group_get(user: CustomUser, group_id: uuid):
    group = get_object_or_404(Group, id=group_id)
    if user.role != 'admin' and not group.users.count(user.pk): 
        return HttpResponse(status=401)
    chats = list(group.chat.all().values("id", "username", "message", "createdAt", "replyTo"))
    for chat in chats:
        chatUser = CustomUser.objects.get(username=chat["username"])
        chat["profile_picture"] = user.profile_picture.url if user.profile_picture else "https://cdn-icons-png.flaticon.com/512/847/847969.png"
        chat["is_me"] = chatUser.username == user.username
    return JsonResponse({"data": chats}, status=200)

def operate_chat_by_group_post(request: HttpRequest, group_id: uuid):
    data = json.loads(request.body)
    user = request.user
    group = get_object_or_404(Group, id=group_id)
    if user.role != 'admin' and not group.users.count(user.pk): 
        return HttpResponse(status=401)
    chat = ChatForm({
        "group_id": group_id,
        "username": user.username,
        "message": data["message"],
        "replyTo": data["replyTo"]
        })
    if chat.is_valid():
        chat.save()
        return HttpResponse(status=201)
    return JsonResponse({"errors": chat.errors}, status=400)

@csrf_exempt
def operate_chat_by_group_patch(request: HttpRequest, chat_id: uuid):
    user = request.user
    data = json.loads(request.body)

    print("here 4")

    new_message = data.get("message", "").strip()

    if not chat_id or not new_message:
        return JsonResponse(
            {"error": "chat_id dan message wajib diisi"},
            status=400
        )

    # Ambil chat
    chat = get_object_or_404(Chat, id=chat_id)

    # Permission check
    if user.role != "admin" and chat.username.username != user.username:
        return HttpResponse(status=403)

    print("reach here 1")
    # Update message saja
    chat.message = new_message
    chat.save(update_fields=["message"])

    print("reach here 2")
    # Response payload (biar Flutter bisa langsung update state)
    response_data = {
        "id": str(chat.id),
        "username": chat.username.username,
        "message": chat.message,
        "createdAt": chat.createdAt,
        "replyTo": chat.replyTo,
        "profile_picture": (
            user.profile_picture.url
            if user.profile_picture
            else "https://cdn-icons-png.flaticon.com/512/847/847969.png"
        ),
        "is_me": True,
    }

    return JsonResponse({"data": response_data}, status=200)

@csrf_exempt
def operate_chat_by_group_delete(request: HttpRequest, group_id: uuid = None, chat_id: uuid = None):
    user = request.user
    if user.role == 'admin':
        Chat.objects.filter(group_id=group_id).delete()
        return HttpResponse(status=204)

    chat = get_object_or_404(Chat, id=chat_id, username=user)
    chat.delete()
    return HttpResponse(status=204)