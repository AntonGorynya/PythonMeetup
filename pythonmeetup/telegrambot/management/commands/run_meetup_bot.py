from django.core.management.base import BaseCommand
from telegram.error import BadRequest

from pythonmeetup import settings
from ...models import Question, Lecture
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    Filters,
    MessageHandler,
)


class Command(BaseCommand):
    help = 'Телеграм-бот для слушателя'

    def handle(self, *args, **kwargs):
        tg_token = settings.TG_LISTENER_TOKEN
        updater = Updater(token=tg_token, use_context=True)
        dispatcher = updater.dispatcher

        def start(update, context):
            user = update.message.from_user
            context.user_data['user'] = user.first_name
            msg = context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f'***\nДобро пожаловать {context.user_data["user"]}!\n\n***')
            context.user_data['msg'] = msg.message_id
            context.user_data['status'] = "FIRST"

            keyboard = [
                [
                    InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')
                ],
                [
                    InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text=f"Мы рады Вас приветствовать в сервисе PythonMeetup. \n",
                reply_markup=reply_markup
            )
            return 'FIRST'

        def start_over(update, context):
            context.user_data['status'] = 'FIRST'
            query = update.callback_query
            query.answer()
            keyboard = [
                [
                    InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')
                ],
                [
                    InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="Мы рады Вас приветствовать в сервисе PythonMeetup.", reply_markup=reply_markup)
            return 'FIRST'

        def get_schedule_events(update, context):
            context.user_data['status'] = 'FIRST'
            date = datetime.date.today()
            event_schedule = ''
            lecture_data = Lecture.objects.all()
            for i, item in enumerate(lecture_data, 1):
                if item.date == date:
                    if i == 1:
                        str_str = f'\nМероприятие: {item.event} \n Рассписание на {date} \n'
                        event_schedule = event_schedule + str_str
                    str_str = f'{i}. {item.topic}, Докладчик: {str(item.speaker).split(" ")[0]}, Время проведения: {item.start_time} - {item.end_time} \n'
                    event_schedule = event_schedule + str_str
                else:
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                                  text=f'***\nРассписание на {date} отсутствует!\n\n****')
            query = update.callback_query
            query.answer()
            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text="Мы рады Вас приветствовать в сервисе PythonMeetup.",
                                    reply_markup=reply_markup)
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                          text=f'***\n{event_schedule}\n\n****')

            return 'SECOND'

        def get_question(update, context):
            context.user_data['status'] = 'SECOND'
            query = update.callback_query
            query.answer()
            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="Мы рады Вас приветствовать в сервисе PythonMeetup.", reply_markup=reply_markup
            )
            context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                          text=f'***\nНапишите Ваш вопрос по текущему докладу:\n\n****')
            return 'SECOND'

        def echo(update: Update, context: CallbackContext) -> None:
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=update.message.message_id)
            if context.user_data['status'] == 'SECOND':
                try:
                    create_questions(update.message.text)
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                                  text=f'***\n{context.user_data["user"]}, \n Ваш вопрос:\n" {update.message.text} "\n ОТПРАВЛЕН!\n\n***')
                except Exception:
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                                  text=f'***\nВаш вопрос не отправлен, отсутствуют активные доклады!\n\n***')
            else:
                try:
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                                  text=f'***\n{context.user_data["user"]}, Ваш сообщение УДАЛЕНО!\n'
                                                       f'Если Вы хотите задать вопрос перейдите в разде:\n'
                                                       f'"Задать вопрос по текущему докладу"\n\n***')

                except BadRequest:
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                                  text=f'***\n{context.user_data["user"]}, Ваш сообщение УДАЛЕНО!\n'
                                                       f'Если Вы хотите задать вопрос перейдите в разде:\n'
                                                       f'"Задать вопрос по текущему докладу"\n\n****')

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