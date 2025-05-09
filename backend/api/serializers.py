from rest_framework import serializers
from recipes.models import Ingredient, Recipe, RecipeIngredient, \
    Favorite, ShoppingCart
from users.models import Subscription
from core.fields import Base64ImageField
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'avatar', 'is_subscribed'
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.subscribers.filter(id=request.user.id).exists()

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get('request')
        if (request and request.method == 'POST'
                and request.path in ['/api/users/',
                                     '/api/users']):
            rep.pop('avatar', None)
            rep.pop('is_subscribed', None)
        return rep


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    image = Base64ImageField(
        allow_null=False,
        allow_empty_file=False,
    )
    text = serializers.CharField()
    cooking_time = serializers.IntegerField(min_value=1)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart'
        ]

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент.')
        ingredient_ids = [item['id'] for item in value]
        for item in value:
            if int(item['amount']) < 1:
                raise serializers.ValidationError(
                    f"Количество ингредиента с ID {item['id']} \
                    должно быть больше или равно 1."
                )
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        existing_ids = Ingredient.objects.filter(
            id__in=ingredient_ids).values_list('id', flat=True)
        missing_ids = set(ingredient_ids) - set(existing_ids)
        if missing_ids:
            raise serializers.ValidationError(
                f'Ингредиенты с ID {missing_ids} не существуют.')
        return value

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                'Поле "text" не может быть пустым.')
        return value

    def create(self, validated_data):
        ingredients_data = self.context['request'].data.get('ingredients', [])
        validated_data.pop('recipeingredient_set', None)

        ingredients_data = self.validate_ingredients(ingredients_data)

        author = validated_data.pop('author', self.context['request'].user)
        recipe = Recipe.objects.create(author=author, **validated_data)

        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=item['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = self.context['request'].data.get('ingredients')

        if ingredients_data is None:
            raise serializers.ValidationError({
                'ingredients': 'Это поле обязательно.'
            })

        validated_data.pop('recipeingredient_set', None)

        if 'image' in validated_data and instance.image:
            instance.image.delete(save=False)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        ingredients_data = self.validate_ingredients(ingredients_data)
        instance.recipeingredient_set.all().delete()
        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item['id'])
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=item['amount']
            )

        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.image:
            ret['image'] = instance.image.url
        else:
            ret['image'] = None
        return ret

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user,
                                           recipe=obj).exists()


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


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='author.avatar', use_url=True,
                                    allow_null=True)

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.author.subscribers.filter(user=request.user).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.author.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(recipes, many=True,
                                     context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
