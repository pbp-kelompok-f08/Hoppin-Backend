# accounts/views.py
import json
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.forms.models import model_to_dict
from django.core import serializers
from .models import CustomUser
from .forms import RegisterForm


def login_page(request):
    return render(request, 'accounts/login.html')

def register_page(request):
    return render(request, 'accounts/register.html')

@login_required
def profile_page(request):
    return render(request, "accounts/profile.html")

@csrf_exempt
def public_profile(request, username):
    # Handle special case for AnonymousUser
    if username.lower() == "anonymous":
        return render(request, "accounts/anonymous_profile.html", status=200)

    user_profile = get_object_or_404(CustomUser, pk=username)
    context = {
        "user_profile": user_profile,
        "is_own_profile": request.user.is_authenticated and request.user.username == username,
    }
    return render(request, "accounts/public_profile.html", context)

@require_POST
@csrf_exempt
def login_ajax(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'}, status=400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return JsonResponse({'success': False, 'message': 'Username dan password wajib diisi'}, status=400)

    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return JsonResponse({'success': True, 'role': user.role})
    return JsonResponse({'success': False, 'message': 'Username atau password salah'}, status=400)


@require_POST
@csrf_exempt
def register_ajax(request: HttpRequest):
    data = json.loads(request.body)
    if not hasattr(request.user, "role") or request.user.role != "admin":
        data["role"] = "user"
    form = RegisterForm(data)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@login_required
def dashboard(request: HttpRequest):
    print(f"username: {request.user.username}, role: {request.user.role}")
    if request.user.role == 'admin':
        users = CustomUser.objects.all()
        return render(request, 'accounts/dashboard_admin.html', {'users': users})
    return render(request, 'accounts/dashboard_user.html')

@login_required
def ajax_all_users(request: HttpRequest):
    if request.user.role != 'admin':
        return HttpResponse(status=401)
    users = serializers.serialize("json", CustomUser.objects.filter(role='user'))
    admins = serializers.serialize("json", CustomUser.objects.filter(role='admin'))
    return JsonResponse({
        "users": json.loads(users),
        "admins": json.loads(admins)
    }, status=200)

@require_GET
def profile(request: HttpRequest):
    user = request.user
    if not user:
        return HttpRequest(status=401)
    data = model_to_dict(user)
    data["participation"] = user.participation
    print(data)
    return JsonResponse({"data": data}, status=200)

@login_required
def admin_delete_user(request, user_id):
    if request.user.role != 'admin':
        return JsonResponse({'success': False}, status=401)
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return JsonResponse({'success': True})

@login_required
def logout_ajax(request):
    logout(request)
    return JsonResponse({'success': True})

@require_GET
@login_required
def profile_detail(request: HttpRequest):
    user = request.user
    data = model_to_dict(user, fields=[
        'username', 'email', 'bio', 'role',
        'favorite_sport', 'skill_level'
    ])
    data["id"] = user.pk
    data["profile_picture"] = user.profile_picture.url if user.profile_picture else None
    data["date_joined"] = user.date_joined.isoformat()
    return JsonResponse({"data": data}, status=200)

@login_required
@require_POST
@csrf_exempt
def update_profile(request):
    user = request.user

    username = user.username  
    email = request.POST.get("email", "").strip()
    bio = request.POST.get("bio", "").strip()
    favorite_sport = request.POST.get("favorite_sport", "").strip()
    skill_level = request.POST.get("skill_level", "").strip()
    profile_picture = request.FILES.get("profile_picture")
    remove_picture = request.POST.get("remove_picture")

    if email and email != user.email and CustomUser.objects.filter(email=email).exists():
        return JsonResponse({"status": "error", "message": "Email already taken."}, status=400)

    if email:
        user.email = email
    user.bio = bio
    user.favorite_sport = favorite_sport or None
    user.skill_level = skill_level or None

    if remove_picture == "true":
        if user.profile_picture:
            user.profile_picture.delete(save=False)
        user.profile_picture = None
    elif profile_picture:
        if user.profile_picture and user.profile_picture.name != profile_picture.name:
            user.profile_picture.delete(save=False)
        user.profile_picture = profile_picture

    user.save()

    return JsonResponse({
        "status": "success",
        "data": {
            "username": user.username,
            "email": user.email,
            "bio": user.bio,
            "favorite_sport": user.favorite_sport,
            "skill_level": user.skill_level,
            "profile_picture": user.profile_picture.url if user.profile_picture else None,
        }
    })

@login_required
@require_POST
@csrf_exempt
def delete_account(request):
    """Delete the current user's account after password confirmation"""
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        if not password:
            return JsonResponse({
                'success': False, 
                'message': 'Password is required for confirmation'
            }, status=400)
        
        # Verify password
        user = authenticate(username=request.user.username, password=password)
        if not user:
            return JsonResponse({
                'success': False, 
                'message': 'Incorrect password'
            }, status=401)
        
        # Store username before deletion
        username = request.user.username
        
        # Logout first, then delete
        logout(request)
        user.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Account {username} has been deleted successfully'
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }, status=500)
    
@login_required
@require_POST
@csrf_exempt
def update_profile_flutter(request):
    """Update profile from Flutter (without file upload)"""
    try:
        data = json.loads(request.body)
        user = request.user
        
        email = data.get("email", "").strip()
        bio = data.get("bio", "").strip()
        favorite_sport = data.get("favorite_sport", "").strip()
        skill_level = data.get("skill_level", "").strip()
        
        # Check email uniqueness
        if email and email != user.email and CustomUser.objects.filter(email=email).exists():
            return JsonResponse({
                "success": False, 
                "message": "Email already taken."
            }, status=400)
        
        # Update fields
        if email:
            user.email = email
        user.bio = bio
        user.favorite_sport = favorite_sport or None
        user.skill_level = skill_level or None
        user.save()
        
        return JsonResponse({
            "success": True,
            "data": {
                "username": user.username,
                "email": user.email,
                "bio": user.bio,
                "favorite_sport": user.favorite_sport,
                "skill_level": user.skill_level,
                "profile_picture": user.profile_picture.url if user.profile_picture else None,
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "message": "Invalid JSON"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "message": str(e)
        }, status=500)
    
@login_required
@require_POST
@csrf_exempt
def upload_profile_picture(request):
    """Upload or update profile picture"""
    try:
        user = request.user
        profile_picture = request.FILES.get("profile_picture")
        
        if not profile_picture:
            return JsonResponse({
                "success": False,
                "message": "No image provided"
            }, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return JsonResponse({
                "success": False,
                "message": "Invalid file type. Only images allowed."
            }, status=400)
        
        # Validate file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            return JsonResponse({
                "success": False,
                "message": "File too large. Max 5MB."
            }, status=400)
        
        # Delete old profile picture if exists
        if user.profile_picture:
            user.profile_picture.delete(save=False)
        
        # Save new picture
        user.profile_picture = profile_picture
        user.save()
        
        return JsonResponse({
            "success": True,
            "message": "Profile picture updated successfully",
            "data": {
                "profile_picture": user.profile_picture.url
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error uploading image: {str(e)}"
        }, status=500)


@login_required
@require_POST
@csrf_exempt
def remove_profile_picture(request):
    """Remove profile picture"""
    try:
        user = request.user
        
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save()
            
            return JsonResponse({
                "success": True,
                "message": "Profile picture removed successfully"
            }, status=200)
        else:
            return JsonResponse({
                "success": False,
                "message": "No profile picture to remove"
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error removing image: {str(e)}"
        }, status=500)

@require_GET
@csrf_exempt
def public_profile_json(request, username):
    """Get public profile data in JSON format for Flutter"""
    try:
        # Handle anonymous user
        if username.lower() == "anonymous":
            return JsonResponse({
                "success": True,
                "data": {
                    "username": "Anonymous",
                    "email": "anonymous@example.com",
                    "bio": "Anonymous user",
                    "profile_picture": None,
                    "favorite_sport": None,
                    "skill_level": None,
                    "date_joined": None,
                    "is_anonymous": True
                }
            }, status=200)
        
        user_profile = get_object_or_404(CustomUser, username=username)
        
        data = {
            "username": user_profile.username,
            "email": user_profile.email,
            "bio": user_profile.bio,
            "profile_picture": user_profile.profile_picture.url if user_profile.profile_picture else None,
            "favorite_sport": user_profile.favorite_sport,
            "skill_level": user_profile.skill_level,
            "date_joined": user_profile.date_joined.isoformat(),
            "is_own_profile": request.user.is_authenticated and request.user.username == username,
            "is_anonymous": False
        }
        
        return JsonResponse({
            "success": True,
            "data": data
        }, status=200)
        
    except CustomUser.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "User not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

