import base64
import uuid

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, \
    IsAuthenticatedOrReadOnly

from django.core.files.base import ContentFile
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse

from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import Ingredient, Recipe, Favorite, \
    ShoppingCart, ShortLink, RecipeIngredient

from users.models import Subscription

from api.serializers import IngredientSerializer, RecipeSerializer, \
    UserSerializer, ShortLinkSerializer, SubscriptionSerializer, \
    ShortRecipeSerializer

from recipes.functions import generate_short_code

from .permissions import IsAuthorOrReadOnly
from .filters import RecipeFilter

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = self.get_object()

        if user == author:
            return Response(
                {'errors': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            try:
                subscription = Subscription.objects.create(user=user,
                                                           author=author)
            except IntegrityError:
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(subscription,
                                                context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(user=user,
                                                       author=author)
            if not subscription.exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True,
                                                context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(subscriptions, many=True,
                                            context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class AvatarUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        avatar_data = request.data.get('avatar')

        if not avatar_data:
            return Response({'error': 'Поле avatar обязательно'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not avatar_data.startswith('data:image'):
            return Response({'error': 'Неверный формат base64-изображения'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            img_data = base64.b64decode(imgstr)
            file_name = f"{uuid.uuid4()}.{ext}"
        except Exception:
            return Response({'error': 'Ошибка обработки изображения'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.avatar = ContentFile(img_data, name=file_name)
        user.save()
        return Response({'avatar': user.avatar.url}, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        if not user.avatar:
            return Response(
                {'error': 'Аватар отсутствует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.avatar.delete(save=False)
        user.avatar = None
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related(
        'recipeingredient_set__ingredient')
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            return Response(
                {'errors': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            try:
                Favorite.objects.create(user=user, recipe=recipe)
            except IntegrityError:
                return Response(
                    {'errors': 'Этот рецепт уже в вашем избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShortRecipeSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite_item = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite_item.exists():
                return Response(
                    {'errors': 'Этот рецепт не находится в вашем избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = self.get_object()

        if request.method == 'POST':
            try:
                ShoppingCart.objects.create(user=user, recipe=recipe)
            except IntegrityError:
                return Response(
                    {'errors': 'Этот рецепт уже в вашей корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShortRecipeSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart_item.exists():
                return Response(
                    {'errors': 'Этот рецепт не находится в вашей корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated])
    def remove_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = self.get_object()
        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)
        if not shopping_cart.exists():
            return HttpResponse(
                'Ваша корзина пуста.',
                content_type='text/plain; charset=utf-8',
                status=status.HTTP_200_OK
            )
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        content = 'Список покупок:\n'
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            content += f'- {name}: {amount} {unit}\n'
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = ShortLink.objects.filter(recipe=recipe).first()
        if not short_link:
            while True:
                short_code = generate_short_code()
                if not ShortLink.objects.filter(
                        short_code=short_code).exists():
                    break
            short_link = ShortLink.objects.create(
                recipe=recipe,
                short_code=short_code
            )
        serializer = ShortLinkSerializer(short_link,
                                         context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
