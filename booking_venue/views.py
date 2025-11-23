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


@login_required
def book_venue(request, venue_id):
    """
    View untuk melakukan booking stadion tertentu.
    - Menolak booking jika waktu sudah terpakai.
    - Menyimpan booking baru jika valid.
    """
    venue = get_object_or_404(Venue, id=venue_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            time = form.cleaned_data['time']

            booking = Booking(
                user=request.user,
                venue=venue,
                date=date,
                time=time,
                status='pending'
            )

            try:
                booking.save()
                messages.success(request, f'Booking stadion {venue.name} berhasil!')
                return redirect('booking_success')
            except Exception as e:
                messages.error(request, f'Error saving booking: {e}')
    else:
        form = BookingForm()

    return render(request, 'book_venue.html', {'form': form, 'venue': venue})

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
        bookings = Booking.objects.all()

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
    
@require_GET
@csrf_exempt
def filter_venues_api(request):
    """
    API untuk memfilter venue berdasarkan region dan alphabet.
    """
    venues = Venue.objects.all()

    region_filter = request.GET.get('region', '')
    alphabet_filter = request.GET.get('alphabet', '')

    if region_filter:
        venues = venues.filter(location__icontains=region_filter)

    if alphabet_filter:
        if alphabet_filter.lower() == 'other':
            venues = venues.exclude(name__regex=r'^[A-Za-z]')
        else:
            venues = venues.filter(name__istartswith=alphabet_filter)

    venue_list = [
        {
            "id": v.id,
            "name": v.name,
            "location": v.location,
            "capacity": v.capacity,
            "price": str(v.price),
        }
        for v in venues
    ]

    return JsonResponse({
        "venues": venue_list,
        "current_region": region_filter,
        "current_alphabet": alphabet_filter,
    }, status=200)