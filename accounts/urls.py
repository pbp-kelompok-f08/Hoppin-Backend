from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    # Web Pages
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Profile - Specific paths FIRST
    path('profile/', profile_page, name='profile_page'),
    path('profile-detail/', profile_detail, name='profile_detail'),
    path('profile/update-flutter/', update_profile_flutter, name='update_profile_flutter'),
    path('profile/upload-picture/', upload_profile_picture, name='upload_profile_picture'),
    path('profile/remove-picture/', remove_profile_picture, name='remove_profile_picture'),
    
    # AJAX Endpoints
    path('ajax/login/', login_ajax, name='login_ajax'),
    path('ajax/register/', register_ajax, name='register_ajax'),
    path('ajax/logout/', logout_ajax, name='logout_ajax'),
    path('ajax/delete-user/<int:user_id>/', admin_delete_user, name='admin_delete_user'),
    path('ajax/users/', ajax_all_users, name='ajax_all_users'),
    path('ajax/profile/', profile, name='profile'),
    path('ajax/update_profile/', update_profile, name='update_profile'),
    
    # Account Management
    path('delete-account/', delete_account, name='delete_account'),
    
    # Generic paths with parameters
    path('profile/<str:username>/json/', public_profile_json, name='public_profile_json'),
    path('profile/<str:username>/', public_profile, name='public_profile'),
]