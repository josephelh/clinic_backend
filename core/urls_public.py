from django.contrib import admin
from django.urls import path, include
from users.views import CustomTokenObtainPairView # Import the view directly
from rest_framework_simplejwt.views import TokenRefreshView

print("[PUBLIC] URLS LOADED (Public Schema)")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints (Directly assigned, no circular 'include')
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    
]