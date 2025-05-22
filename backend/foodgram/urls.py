from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from api.views import redirect_short_link


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(
        r'^s/(?P<short_code>[a-zA-Z0-9]{4})/$',
        redirect_short_link
    ),
    path('api/', include('api.urls')),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
