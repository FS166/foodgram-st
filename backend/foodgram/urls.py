from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import get_object_or_404, redirect
from recipes.models import ShortLink


def redirect_short_link(request, short_code):
    print(f"Redirecting short code: {short_code}")
    short_link = get_object_or_404(ShortLink, short_code=short_code)
    recipe_url = f"/api/recipes/{short_link.recipe.id}/"
    return redirect(recipe_url)


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
