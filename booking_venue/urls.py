from django.urls import path
from . import views

app_name = "booking_venue"

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('book/<uuid:venue_id>/', views.book_venue, name='book_venue'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel/<uuid:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('show-venue-json/', views.api_venues, name='api_venues'),
    path('show-bookings-json/', views.api_bookings, name='api_bookings'),
    path('filter-venues-api/', views.filter_venues_api, name='filter_venues_api'),
]
