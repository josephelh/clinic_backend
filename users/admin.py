from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class MyUserAdmin(UserAdmin):
    # Add our custom 'role' field to the admin interface
    fieldsets = UserAdmin.fieldsets + (
        ('Clinic Info', {'fields': ('role', 'clinic_id')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')