from django_filters import rest_framework as filters
from recipes.models import Recipe
from django.contrib.auth import get_user_model

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ['author', 'is_in_shopping_cart']

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset.exclude(in_shopping_cart__user=self.request.user)

    def filter_is_favorited(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset
        if value:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset.exclude(favorited_by__user=self.request.user)
