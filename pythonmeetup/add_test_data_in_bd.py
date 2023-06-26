import datetime
import os
import random
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonmeetup.settings')
django.setup()

from django.utils import timezone
from faker import Faker
from telegrambot.models import Event, Lecture, Question, Listener


def create_listeners():
    for _ in range(10):
        nickname = fake.user_name()[:30]
        isspeaker = random.choice([True, False])
        listener = Listener.objects.create(
            nickname=nickname,
            isspeaker=isspeaker
        )
        listener.save()


def create_events():
    for _ in range(5):
        name = fake.word()
        description = fake.sentence()
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=random.randint(1, 5))
        Event.objects.create(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date)


def create_lectures():
    events = Event.objects.all()
    users = Listener.objects.filter(isspeaker=True)

    for event in events:
        for _ in range(3):
            speaker = random.choice(users)
            topic = fake.sentence()
            date = event.start_date + timezone.timedelta(
                days=random.randint(0, (event.end_date - event.start_date).days))
            start_time_str = fake.time()
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M:%S').time()
            end_time = (datetime.datetime.combine(datetime.datetime.today(), start_time) +
                        datetime.timedelta(minutes=random.randint(30, 120))).time()
            is_finished = random.choice([True, False])
            Lecture.objects.create(
                topic=topic,
                date=date,
                start_time=start_time,
                end_time=end_time,
                speaker=speaker,
                isfinished=is_finished,
                event=event
            )


def create_questions():
    lectures = Lecture.objects.all()
    users = Listener.objects.all()

    for lecture in lectures:
        for _ in range(random.randint(0, 5)):
            listener = random.choice(users)
            text = fake.sentence()
            answered = random.choice([True, False])
            Question.objects.create(
                listener=listener,
                lecture=lecture,
                text=text,
                answered=answered
            )


def main():

    try:
        create_listeners()
        create_events()
        create_lectures()
        create_questions()
        print("Тестовые данные созданы")
    except Exception as error:
        print(f"Произошла ошибка при создании тестовых данных: {str(error)}")


if __name__ == '__main__':
    fake = Faker('ru_RU')
    main()
