from django.urls import include, path

urlpatterns = [
    path('auth/', include('apps.users.urls')),
    path('', include('apps.services.urls')),
    path('', include('apps.bookings.urls')),
]
