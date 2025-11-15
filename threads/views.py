# threads/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponse,HttpResponseRedirect

from accounts.models import CustomUser
from .models import Thread,ReplyChild

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

from django.templatetags.static import static



@login_required
def show_main(request):
    return render(request, "main_threads.html")

def show_json(request):
    thread_list = Thread.objects.all().order_by('-created_at')
    data = [
        {
            'user':{
                'username': getattr(thread.user, 'username', 'Anonymous'),
                'profile_picture': (
                    thread.user.profile_picture.url
                    if getattr(thread.user, 'profile_picture', None) and hasattr(thread.user.profile_picture, 'url')
                    else static('accounts/img/default.png')
                )
            },
            'id': str(thread.id),
            'content' :thread.content,
            'tags' : thread.tags,
            'image' : thread.image,
            'likeCount' : thread.likeCount,
            'shareCount' : thread.shareCount,
            'replyCount' : thread.replyCount,
            'created_at' : thread.created_at,
            "isLiked": request.user in thread.liked_by.all()
        }
        for thread in thread_list
    ]
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
@require_POST
def add_thread_entry_ajax(request):
    user = request.user
    content = request.POST.get("content")
    tags = request.POST.get("tags")
    image = request.POST.get("image")

    new_thread = Thread(
        user=user,
        content = content,
        tags =  tags,
        image = image,
    )
    new_thread.save()
    return HttpResponse(b"CREATED", status=201)

def delete_thread(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    thread.delete()
    return HttpResponseRedirect(reverse('threads:show_main'))


def get_replies_by_threadId(request, threadId):
    replies = ReplyChild.objects.filter(thread=threadId).order_by('-likeCount')

    data = [
        {
            'user':{
                'username': getattr(reply.user, 'username', 'Anonymous'),
                'profile_picture': (
                    reply.user.profile_picture.url
                    if getattr(reply.user, 'profile_picture', None) and hasattr(reply.user.profile_picture, 'url')
                    else static('accounts/img/default.png')
                )
            },
            'id': str(reply.id),
            'thread_id': str(reply.thread.id),
            'content': reply.content,
            'created_at': reply.created_at.isoformat(),
            'likeCount': reply.likeCount,
            "isLiked": request.user in reply.liked_by.all()

        }
        for reply in replies
    ]

    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
@require_POST
def add_reply_entry_ajax(request, threadId):
    content = request.POST.get("content", "").strip()
    parent_thread = Thread.objects.get(pk=threadId)
    parent_thread.changeReply(True)

    reply = ReplyChild.objects.create(
        thread=parent_thread,
        content=content,
        user = request.user
    )

    data = {
        "id": reply.id,
        "thread_id": reply.thread.id,
        "content": reply.content,
        "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "likeCount": reply.likeCount,
        "count":parent_thread.replyCount,
        'user':{
                'username': getattr(reply.user, 'username', 'Anonymous'),
                'profile_picture': (
                    reply.user.profile_picture.url
                    if getattr(reply.user, 'profile_picture', None) and hasattr(reply.user.profile_picture, 'url')
                    else static('accounts/img/default.png')
                )
            },
    }

    return JsonResponse(data, status=201)

@login_required
@csrf_exempt
@require_POST
def like_thread_ajax(request, thread_id):

    thread = Thread.objects.get(pk=thread_id)
    user = request.user
    isLiked = thread.changeLike(user)
    data = {
        "likeCount":thread.likeCount,
        "isLiked": isLiked
    }
    return JsonResponse(data)

@login_required
@csrf_exempt
@require_POST
def like_reply_ajax(request, replyId):
    reply = ReplyChild.objects.get(pk=replyId)
    user = request.user
    isLiked = reply.changeLike(user)
    data = {
        "likeCount":reply.likeCount,
        "isLiked": isLiked
    }
    return JsonResponse(data)


def delete_reply(request, reply_id):
    reply = get_object_or_404(ReplyChild, pk=reply_id)
    reply.thread.changeReply(False)
    reply.delete()
    return HttpResponseRedirect(reverse('threads:show_main'))

