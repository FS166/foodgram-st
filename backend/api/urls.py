from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet, IngredientViewSet, RecipeViewSet, \
    AvatarUpdateView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('users/me/avatar/', AvatarUpdateView.as_view(), name='avatar-update'),
    path('recipes/<int:pk>/get-link/',
         RecipeViewSet.as_view({'get': 'get_link'}))

]
