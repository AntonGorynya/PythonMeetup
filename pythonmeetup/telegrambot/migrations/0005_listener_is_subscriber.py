# Generated by Django 4.2.2 on 2023-06-25 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegrambot', '0004_rename_user_question_listener'),
    ]

    operations = [
        migrations.AddField(
            model_name='listener',
            name='is_subscriber',
            field=models.BooleanField(default=True),
        ),
    ]