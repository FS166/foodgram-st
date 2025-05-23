from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ['author', 'is_in_shopping_cart', 'is_favorited']

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
