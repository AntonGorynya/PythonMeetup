from django.core.management.base import BaseCommand
from pythonmeetup import settings
from ...models import User, Question, Lecture, Event
import datetime
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    LabeledPrice
)
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

class Command(BaseCommand):
    help = 'Телеграм-бот для спикеров'
    def handle(self, *args, **kwargs):
        tg_token = settings.TG_SPEAKER_TOKEN
        updater = Updater(token=tg_token, use_context=True)
        dispatcher = updater.dispatcher

        def start_conversation(update, _):
            query = update.callback_query
            print(datetime.datetime.now().time())

            lecture = Lecture.objects.filter(
                date=datetime.date.today(),
                isfinished=False,
                start_time__lte=datetime.datetime.now().time()
            ).first()
            print(lecture)

            keyboard = [
               [
                   InlineKeyboardButton("Перейти к вопросам", callback_data='to_questions'),
               ],
               [
                   InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
               ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.message:
                username = update.message.from_user.username
                update.message.reply_text(
                   text=f"Добрый день {username}. По вашей лекции есть N вопросов", reply_markup=reply_markup,
                   parse_mode=ParseMode.HTML
                )
            else:
                username = query.message.chat['username']
                query.edit_message_text(
                    text=f"Добрый день {username}. По вашей лекции есть N вопросов", reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return 'GREETINGS'
        def show_question(update, _):
            query = update.callback_query

            keyboard = [
               [
                   InlineKeyboardButton("<<", callback_data='back'),
                   InlineKeyboardButton(">>", callback_data='forward'),
               ],
               [
                   InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
               ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
               text=f"Тут будет текст вопроса", reply_markup=reply_markup,
               parse_mode=ParseMode.HTML
            )
            return 'GREETINGS'

        def cancel(update, _):
           update.message.reply_text(
               'До новых встреч',
               reply_markup=ReplyKeyboardRemove()
           )
           return ConversationHandler.END

        def end_conversation(update, _):
            query = update.callback_query

            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            query.edit_message_text(
                text=f"Лекция завершена", reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'GREETINGS'

        conv_handler = ConversationHandler(
           entry_points=[CommandHandler('start', start_conversation)],
           states={
               'GREETINGS': [
                   CallbackQueryHandler(end_conversation, pattern='to_end_lecture'),
                   CallbackQueryHandler(show_question, pattern='to_questions'),
                   CallbackQueryHandler(start_conversation, pattern='to_start'),
               ],
           },
           fallbacks=[CommandHandler('cancel', cancel)]
        )

        dispatcher.add_handler(conv_handler)
        dispatcher.add_handler(CommandHandler('start', start_conversation))
        updater.start_polling()
        updater.idle()