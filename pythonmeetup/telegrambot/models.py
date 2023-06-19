from django.db import models


class User(models.Model):
    nickname = models.CharField(max_length=500, verbose_name='Никнейм клиента', unique=True)
    isspeaker = models.BooleanField(default=False, verbose_name='Является спикером?')

    def __str__(self):
        return self.nickname


class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question')
    text = models.CharField(max_length=500, verbose_name='Вопрос')
    answered = models.BooleanField(default=False, verbose_name='Отвечен?')

    def __str__(self):
        return f'{self.user} Q: {self.id}'


class Event(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название мероприятия')
    description = models.CharField(max_length=500, verbose_name='Описание мероприятия', blank=True)
    start_date = models.DateField(verbose_name='Начало')
    end_date = models.DateField(verbose_name='Окончание')

    def __str__(self):
        return f'{self.name} {self.start_date} - {self.end_date}'


class Lecture(models.Model):
    topic = models.CharField(max_length=30, verbose_name='Название доклада')
    date = models.DateField(verbose_name='Дата доклада')
    start_time = models.TimeField(verbose_name='Начало доклада')
    end_time = models.TimeField(verbose_name='Окончание доклада')
    speaker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lectures', verbose_name='Спикер')
    isfinished = models.BooleanField(default=False, verbose_name='Доклад завершен?')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='lectures', verbose_name='Мероприятие')

    def __str__(self):
        return f'{self.speaker} {self.date} {self.start_time} - {self.end_time}'
