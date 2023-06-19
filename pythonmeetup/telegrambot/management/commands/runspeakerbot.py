from django.core.management.base import BaseCommand

class Command(BaseCommand):
   help = 'Телеграм-бот для спикеров'

   def handle(self, *args, **kwargs):
       print(*args)
       print(**kwargs)