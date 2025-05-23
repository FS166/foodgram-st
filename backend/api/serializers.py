from rest_framework import serializers
from django.contrib.auth import get_user_model

from core.fields import Base64ImageField
from recipes.constants import MIN_COOKING_TIME, MIN_INGREDIENT_FROM_RECIPES
from recipes.models import Ingredient, Recipe, RecipeIngredient

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.ImageField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar',
            'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.subscribers.filter(id=request.user.id).exists()


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'password',
            'avatar')

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        if 'avatar' in validated_data:
            user.avatar = validated_data['avatar']
        user.save()
        return user


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngredientWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_FROM_RECIPES)

    def validate(self, data):
        if data['amount'] < MIN_INGREDIENT_FROM_RECIPES:
            raise serializers.ValidationError(
                f"Количество ингредиента должно быть больше или равно "
                f"{MIN_INGREDIENT_FROM_RECIPES}."
            )
        return data


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set',
                                             many=True, read_only=True)
    image = serializers.ImageField(use_url=True, read_only=True)
    author = UserReadSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author', 'name', 'image', 'text', 'cooking_time',
            'ingredients', 'is_favorited', 'is_in_shopping_cart'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.in_shopping_cart.filter(user=request.user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(allow_null=False, allow_empty_file=False)
    text = serializers.CharField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = ['name', 'image', 'text', 'cooking_time', 'ingredients']

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.')
        ingredient_ids = [item['ingredient'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        return value

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                'Поле "text" не может быть пустым.')
        return value

    def add_ingredients_to_recipe(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        self.add_ingredients_to_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        if instance.image and 'image' in validated_data:
            instance.image.delete(save=False)
        instance = super().update(instance, validated_data)
        instance.recipeingredient_set.all().delete()
        self.add_ingredients_to_recipe(instance, ingredients_data)
        return instance


class ShortLinkSerializer(serializers.Serializer):
    short_link = serializers.SerializerMethodField()

    def get_short_link(self, obj):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError('Пустой контекст')
        base_url = request.build_absolute_uri('/s/')
        return f"{base_url}{obj.short_code}"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['short-link'] = ret.pop('short_link')
        return ret


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(recipes, many=True,
                                     context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
