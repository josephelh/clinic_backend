from django.contrib import admin
from django.urls import path, include
from users.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

print("[TENANT] URLS LOADED (Clinic Schema)")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # We define login here too so it works on the subdomain
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # This provides /api/auth/users/ (Missing in your public file)
    path('api/auth/', include('users.urls')), 
    
    # This provides /api/medical/...
    path('api/medical/', include('medical.urls')),
]