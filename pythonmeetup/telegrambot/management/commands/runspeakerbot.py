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

        def start_conversation(update, context):
            query = update.callback_query
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
                lecture = get_lecture(username)
                questions = get_questions(lecture)
                context.user_data['questions'] = questions
                context.user_data['lecture'] = lecture
                update.message.reply_text(
                    text=f"Добрый день {username}. По вашей лекции есть {len(questions)} не отвеченных вопрос(a/ов)",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                username = query.message.chat['username']
                query.edit_message_text(
                    text=f"Добрый день {username}. По вашей лекции есть N вопросов", reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return 'GREETINGS'
        def show_question(update, context):
            query = update.callback_query
            questions = context.user_data['questions']
            if 'question_num' not in context.user_data:
                context.user_data['question_num'] = 0
            question = questions[0]
            quantity = len(questions)
            question_num = context.user_data['question_num']

            keyboard = [
                [
                    InlineKeyboardButton("<<", callback_data=-1),
                    InlineKeyboardButton(">>", callback_data=1),
                ],
                [
                    InlineKeyboardButton("Пометить как отмеченный", callback_data='mark'),
                ],
                [
                    InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
                ],
            ]

            if '1' in query['data']:
                question_num = (context.user_data['question_num'] + int(query['data'])) % quantity
                context.user_data['question_num'] = question_num
                question = context.user_data['questions'][question_num]

            if query['data'] == 'mark':
                quantity -= 1
                if quantity > 0:
                    questions = list(questions)
                    pop_question = questions.pop(question_num)
                    pop_question.answered = True
                    print(pop_question.id)
                    context.user_data['questions'] = questions
                    question = questions[question_num % quantity]
            if quantity == 1:
                keyboard = [
                    [
                        InlineKeyboardButton("Пометить как отмеченный", callback_data='mark'),
                    ],
                    [
                        InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
                    ]
                ]
            if quantity == 0:
                keyboard = [
                    [
                        InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
                    ]
                ]


            reply_markup = InlineKeyboardMarkup(keyboard)


            if quantity:
                query.edit_message_text(
                   text=f"{question.user}:\n {question.text}", reply_markup=reply_markup,
                   parse_mode=ParseMode.HTML
                )
            else:
                query.edit_message_text(
                    text=f"Вы ответили на все попроы", reply_markup=reply_markup,
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
                   CallbackQueryHandler(show_question, pattern='to_questions|mark|1|-1'),
                   CallbackQueryHandler(start_conversation, pattern='to_start'),
               ],
           },
           fallbacks=[CommandHandler('cancel', cancel)]
        )

        dispatcher.add_handler(conv_handler)
        dispatcher.add_handler(CommandHandler('start', start_conversation))
        updater.start_polling()
        updater.idle()

def get_lecture(username):
    lecture = Lecture.objects.filter(
        date=datetime.date.today(),
        isfinished=False,
        start_time__lte=datetime.datetime.now().time(),
        speaker__nickname=username
    ).first()
    return lecture

def get_questions(lecture):
    questions = Question.objects.filter(
        lecture=lecture
    )
    return list(questions)