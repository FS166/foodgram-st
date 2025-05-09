from rest_framework import serializers
from recipes.models import Ingredient, Recipe, RecipeIngredient, Subscription, Favorite, ShoppingList
from core.fields import Base64ImageField
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class IngredientSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='name', read_only=True)
    label = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit', 'value', 'label']

class RecipeIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError("Ingredient does not exist.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

class RecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, required=True)
    ingredients_data = RecipeReadSerializer(many=True, read_only=True, source='recipeingredient_set')
    image = Base64ImageField(
        allow_null=False,
        allow_empty_file=False,
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    text = serializers.CharField(write_only=True, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default='')  # description необязательный

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'description', 'text', 'cooking_time',
            'ingredients', 'ingredients_data', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def validate(self, data):
        if 'text' in data and data['text']:
            data['description'] = data.pop('text')  # Преобразуем text в description, если text есть
        return data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return Favorite.objects.filter(user=user, recipe=obj).exists() if user.is_authenticated else False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingList.objects.filter(user=user, recipe=obj).exists() if user.is_authenticated else False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data.pop('text', None)  # Удаляем text после преобразования
        recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient_data['id']),
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data.pop('text', None)
        instance = super().update(instance, validated_data)
        instance.recipeingredient_set.all().delete()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=Ingredient.objects.get(id=ingredient_data['id']),
                amount=ingredient_data['amount']
            )
        return instance