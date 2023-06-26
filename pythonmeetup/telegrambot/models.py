from django.core.exceptions import ValidationError
from django.db import models
from django.forms import JSONField
from telegram import Bot

from pythonmeetup import settings


class Listener(models.Model):
    nickname = models.CharField(max_length=500, verbose_name='Никнейм клиента', unique=True)
    isspeaker = models.BooleanField(default=False, verbose_name='Является спикером?')
    is_subscriber = models.BooleanField(default=True)
    chat_id = models.CharField(max_length=50, verbose_name='Chat ID')

    def __str__(self):
        if self.isspeaker:
            return f'{self.nickname} speaker'
        return f'{self.nickname}'


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
    speaker = models.ForeignKey(Listener, on_delete=models.CASCADE, related_name='lectures', verbose_name='Спикер')
    isfinished = models.BooleanField(default=False, verbose_name='Доклад завершен?')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='lectures', verbose_name='Мероприятие')

    def __str__(self):
        return f'{self.topic} {self.speaker} {self.date} {self.start_time} - {self.end_time}'

    @classmethod
    def validate_time(cls, lecture):
        existing_lectures = cls.objects.filter(date=lecture.date)

        for existing_lecture in existing_lectures:
            if existing_lecture.pk == lecture.pk:
                continue

            if lecture.start_time < existing_lecture.end_time and lecture.end_time > existing_lecture.start_time:
                raise ValidationError('Время доклада пересекается с другим докладом.')

    def clean(self):
        self.validate_time(self)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if not is_new:
            self.send_notification()

    def send_notification(self):
        subscribers = Listener.objects.filter(is_subscriber=True)
        bot = Bot(token=settings.TG_LISTENER_TOKEN)
        for subscriber in subscribers:
            chat_id = subscriber.chat_id

            message = f'Расписание изменилось. Доклад {self.topic} состоится в {self.start_time}'
            bot.send_message(chat_id=chat_id, text=message)


class Question(models.Model):
    listener = models.ForeignKey(Listener, on_delete=models.CASCADE, related_name='questions')
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, verbose_name='Вопрос')
    answered = models.BooleanField(default=False, verbose_name='Отвечен?')

    def __str__(self):
        return f'{self.listener} Q: {self.id}'
