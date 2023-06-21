from django.contrib import admin
from .models import Event, Lecture, Question, Listener

admin.site.register(Event)
admin.site.register(Lecture)
admin.site.register(Question)
admin.site.register(Listener)
