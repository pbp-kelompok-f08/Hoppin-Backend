from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.http import JsonResponse
from django.core import serializers
from .models import Venue, Booking
from .forms import BookingForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
import json

def main_page(request):
    """
    Halaman utama menampilkan daftar venue (stadion) yang bisa dipesan.
    """
    venues = Venue.objects.all()

    region_filter = request.GET.get('region', '')
    alphabet_filter = request.GET.get('alphabet', '')

    if region_filter:
        venues = venues.filter(location__icontains=region_filter)

    if alphabet_filter:
        if alphabet_filter == 'other':
            venues = venues.exclude(name__regex=r'^[A-Za-z]')
        else:
            venues = venues.filter(name__istartswith=alphabet_filter)


    all_venues = Venue.objects.all()
    regions = set()
    for venue in all_venues:
        if ', ' in venue.location:
            country = venue.location.split(', ')[-1]
            regions.add(country)
    regions = sorted(list(regions))

    return render(request, 'main_page.html', {
        'venues': venues,
        'regions': regions,
        'current_region': region_filter,
        'current_alphabet': alphabet_filter
    })


@csrf_exempt
def book_venue(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)

    if request.method == 'GET':
        return render(request, 'book_venue.html', {'venue': venue})
    
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)

        try:
            data = json.loads(request.body)
            date = data.get('date')
            time = data.get('time')
        except json.JSONDecodeError:
            date = request.POST.get('date')
            time = request.POST.get('time')

        if not date or not time:
             return JsonResponse({'success': False, 'message': 'Date and Time are required'}, status=400)

        booking = Booking(
            user=request.user,
            venue=venue,
            date=date,
            time=time,
            status='pending'
        )
        try:
            booking.save()
            return JsonResponse({'success': True, 'message': 'Booking created successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error saving booking: {str(e)}'}, status=500)

@login_required
def my_bookings(request):
    """
    Menampilkan daftar booking milik user yang sedang login.
    """
    bookings = Booking.objects.filter(user=request.user).order_by('-date', '-time')
    return render(request, 'my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, booking_id):
    """
    Menghapus booking jika milik user tersebut.
    """
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        booking.delete()
        messages.success(request, 'Booking telah dibatalkan.')
    return redirect('booking_venue:my_bookings')

# Data delivery for flutter

@csrf_exempt
def api_venues(request):
    """
    API endpoint to get venues data for frontend.
    """
    venues = Venue.objects.all()

    venues_data = []
    for venue in venues:
        venues_data.append({
            'id': str(venue.id),
            'name': venue.name,
            'location': venue.location,
            'capacity': venue.capacity,
            'description': venue.description,
            'price_per_hour': 100.00,
        })

    return JsonResponse({'venues': venues_data})

@csrf_exempt
def api_bookings(request):
    """
    API endpoint to get bookings data for frontend.
    """
    if request.method == 'GET':
        bookings = Booking.objects.filter(user=request.user).order_by('-date', '-time')

        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': str(booking.id),
                'user': booking.user.username,
                'venue': booking.venue.name,
                'date': booking.date.strftime('%Y-%m-%d'),
                'time': booking.time.strftime('%H:%M:%S'),
                'status': booking.status,
            })

        return JsonResponse({'bookings': bookings_data})
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=400)

@csrf_exempt
def api_delete_booking(request, booking_id):
    """
    API endpoint to delete a booking.
    """
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        booking.delete()
        return JsonResponse({'message': 'Booking deleted successfully.'})
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=400)
    
@require_GET
@csrf_exempt
def filter_venues_api(request):
    venues = Venue.objects.all()

    alphabet_filter = request.GET.get('alphabet', '')

    if alphabet_filter:
        if alphabet_filter.lower() == 'other':
            venues = venues.exclude(name__regex=r'^[A-Za-z]')
        else:
            venues = venues.filter(name__istartswith=alphabet_filter)

    venue_list = [
        {
            "id": str(v.id),
            "name": v.name,
            "location": v.location,
            "capacity": v.capacity,
            "description": v.description,
            "price_per_hour": 100.00,   # ✅ pakai field sama
        }
        for v in venues
    ]

    return JsonResponse({"venues": venue_list})