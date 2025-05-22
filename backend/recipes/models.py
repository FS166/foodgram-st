from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator

from .constants import (
    MAX_RECIPE_NAME_LEN,
    MAX_INGREDIENT_NAME_LEN,
    MAX_MEASUREMENT_UNIT_LEN,
    MIN_INGREDIENT_FROM_RECIPES,
    MAX_SHORT_CODE_LEN,
)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_INGREDIENT_NAME_LEN,
                            unique=True,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=MAX_MEASUREMENT_UNIT_LEN)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор',
                               related_name='recipes')
    name = models.CharField(max_length=MAX_RECIPE_NAME_LEN,
                            verbose_name='Название')

    image = models.ImageField(
        upload_to='recipes/images/',
        validators=(
            FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg')),
        ),
        verbose_name='Картинка',
    )
    text = models.TextField(blank=True, verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)')
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Дата создания')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(MIN_INGREDIENT_FROM_RECIPES,
                              'Количество должно быть больше 0')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient.name} ({self.amount} \
         {self.ingredient.measurement_unit})'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в корзину'


class ShortLink(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_links',
        verbose_name='Рецепт'
    )
    short_code = models.CharField(
        max_length=MAX_SHORT_CODE_LEN,
        unique=True,
        verbose_name='Короткий код'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        indexes = [models.Index(fields=['short_code'])]

    def __str__(self):
        return f'{self.short_code} -> Рецепт {self.recipe.id}'
