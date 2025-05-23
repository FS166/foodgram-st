from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
