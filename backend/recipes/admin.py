from django.contrib import admin

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Favorite,
    ShortLink
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    search_fields = ('name', 'author__username')
    readonly_fields = ('favorite_count',)

    def favorite_count(self, obj):
        return obj.favorite_set.count()

    favorite_count.short_description = 'Добавлений в избранное'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added_at')


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'short_code', 'created_at')
