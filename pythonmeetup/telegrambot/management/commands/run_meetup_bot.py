from django.core.management.base import BaseCommand
from pythonmeetup import settings
from django.db import models
from ...models import Listener, Question, Lecture, Event
import datetime
import json
import logging
from django.utils.timezone import localtime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    TypeHandler,
    Filters,
    MessageHandler,
)

# Ведение журнала логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Телеграм-бот для слушателя'

    def handle(self, *args, **kwargs):
        tg_token = settings.TG_LISTENER_TOKEN
        updater = Updater(token=tg_token, use_context=True)
        dispatcher = updater.dispatcher

        def start(update, _):
            user = update.message.from_user
            logger.info("Пользователь %s начал разговор", user.first_name)

            keyboard = [
                [InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')],
                [InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text=f"Мы рады Вас приветствовать {user.first_name} в сервисе PythonMeetup. \n", reply_markup=reply_markup
            )
            return 'FIRST'

        def start_over(update, _):
            query = update.callback_query
            query.answer()
            keyboard = [
                [InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')],
                [InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="Мы рады Вас приветствовать в сервисе PythonMeetup.", reply_markup=reply_markup)
            return 'FIRST'

        def get_schedule_events(update, _):
            date = datetime.date.today()
            schedule = ''
            for i, item in enumerate(Lecture.objects.all(), 1):
                if i == 1:
                    str_str = f'{item.event} \n Рассписание на {date} \n'
                    schedule = schedule + str_str
                if item.date == date:
                    str_str = f'{i}. {item.topic}, Докладчик: {str(item.speaker).split(" ")[0]}, Время проведения: {item.start_time} - {item.end_time} \n'
                    schedule = schedule + str_str
            query = update.callback_query
            query.answer()
            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=f'{schedule}', reply_markup=reply_markup)
            return 'SECOND'

        def get_question(update, context):
            query = update.callback_query
            query.answer()
            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="Напишите Ваш вопрос по текущему докладу:", reply_markup=reply_markup
            )
            return 'SECOND'

        def end(update, _):
            """Возвращает `ConversationHandler.END`, который говорит
            `ConversationHandler` что разговор окончен"""
            query = update.callback_query
            query.answer()
            query.edit_message_text(text="ДО скорой встречи!")
            return ConversationHandler.END

        def echo(update: Update, context: CallbackContext) -> None:
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=update.message.message_id)
            try:
                create_questions(update.message.text)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f' Отправлен Ваш вопрос:\n {update.message.text}')
            except Exception as error:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f'Ваш вопрос не отправлен, отсутствуют активные доклады')
                print(f"Отсутствуют активные доклады: {str(error)}")

        def create_questions(question):
            lectures = Lecture.objects.filter(
                date=datetime.date.today(),
                isfinished=False,
                start_time__lte=datetime.datetime.now().time(),
            )
            if len(lectures) == 0:
                raise Exception
            for lecture in lectures:
                listener = lecture.speaker
                text = question
                answered = False
                Question.objects.create(
                    listener=listener,
                    lecture=lecture,
                    text=text,
                    answered=answered
                )

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={  # словарь состояний разговора, возвращаемых callback функциями
                'FIRST': [
                    CallbackQueryHandler(get_schedule_events, pattern='event_plan'),
                    CallbackQueryHandler(get_question, pattern='to_question'),
                ],
                'SECOND': [
                    CallbackQueryHandler(start_over, pattern='to_start')
                ],
            },
            fallbacks=[CommandHandler('start', start)],
        )

        echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
        dispatcher.add_handler(echo_handler)

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
