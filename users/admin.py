from django.contrib import admin
from users.models import Location, Rooms, Booking
from users.models import User



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'username', 'first_name', 'last_name', 'fullname',
        'language_code', 'deep_link',
        'created_at', 'updated_at', 'is_blocked_bot',
        'is_password', 'is_logging'
    ]
    list_filter = ["is_blocked_bot", ]
    search_fields = ('username', 'user_id')



@admin.register(
    Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'created_at']

@admin.register(
    Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['room_name', 'start_datetime', 'end_datetime', 'user', 'created_at']

@admin.register(
    Rooms)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_id', 'room_name']


