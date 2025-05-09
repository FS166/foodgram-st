from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Удаляет все ингредиенты из базы данных'

    def handle(self, *args, **kwargs):
        count = Ingredient.objects.count()
        if count == 0:
            self.stdout.write(self.style.WARNING(
                'База данных уже пуста: ингредиенты отсутствуют'))
            return

        Ingredient.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'Успешно удалено {count} ингредиентов'))
