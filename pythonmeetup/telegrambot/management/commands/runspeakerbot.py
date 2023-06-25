from django.core.management.base import BaseCommand
from pythonmeetup import settings
from ...models import Listener, Question, Lecture, Event
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
            previous_text = ''
            if update.message:
                username = update.message.from_user.username
            else:
                username = query.message.chat['username']
                previous_text = query.message.text
            lecture = get_lecture(username)
            questions = get_questions(lecture)
            message_text = f'Добрый день {username}. Сегодня у вас нет активных лекций'
            keyboard = [
                [
                    InlineKeyboardButton("Обновить", callback_data='to_start'),
                ],
            ]
            if lecture:
                message_text = f'Добрый день {username}. По вашей лекции есть {questions.count()}' \
                               f' {decline_question(questions.count())}'
                keyboard = [
                    [
                        InlineKeyboardButton("Перейти к вопросам", callback_data='to_questions'),
                    ],
                    [
                        InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
                    ],
                    [
                        InlineKeyboardButton("Обновить", callback_data='to_start'),
                    ],
                ]
            context.user_data['questions'] = questions
            context.user_data['lecture'] = lecture

            reply_markup = InlineKeyboardMarkup(keyboard)
            if message_text != previous_text:
                if update.message:
                    update.message.reply_text(
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    query.edit_message_text(
                        text=message_text, reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
            return 'SPEAKER'

        def show_question(update, context):
            query = update.callback_query
            lecture = context.user_data['lecture']
            questions = get_questions(lecture)
            if 'question_num' not in context.user_data:
                context.user_data['question_num'] = 0
            question_num = context.user_data['question_num']
            quantity = questions.count()

            # Получаем порядковый номер следующего вопроса
            if '1' in query['data']:
                question_num = (question_num + int(query['data'])) % quantity
                context.user_data['question_num'] = question_num
                question = questions[question_num]

            if query['data'] == 'mark':
                question = questions[question_num]
                question.answered = True
                question.save()
                quantity -= 1
                if quantity:
                    context.user_data['question_num'] = question_num % quantity
                    question = questions[context.user_data['question_num']]
                else:
                    context.user_data['question_num'] = 0

            if quantity:
                question = questions[question_num]
                keyboard = [
                    [
                        InlineKeyboardButton("Пометить как отмеченный", callback_data='mark'),
                    ],
                    [
                        InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
                    ],
                ]

            if quantity > 1:
                keyboard.append([
                        InlineKeyboardButton("<<", callback_data=-1),
                        InlineKeyboardButton(">>", callback_data=1),
                    ])
            if quantity == 0:
                keyboard = [
                    [
                        InlineKeyboardButton("Обновить", callback_data='to_start'),
                    ],
                    [
                        InlineKeyboardButton("Завершить лекцию", callback_data='to_end_lecture'),
                    ]
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            if quantity:
                query.edit_message_text(
                    text=f"Вопрос от пользователя @{question.listener.nickname}:\n {question.text}",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                query.edit_message_text(
                    text=f"Вы ответили на все вопросы", reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return 'SPEAKER'

        def cancel(update, _):
            update.message.reply_text(
               'До новых встреч',
               reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

        def end_conversation(update, context):
            query = update.callback_query
            lecture = context.user_data['lecture']
            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            lecture.isfinished = True
            lecture.save()

            query.edit_message_text(
                text=f"Лекция завершена", reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'SPEAKER'

        conv_handler = ConversationHandler(
           entry_points=[CommandHandler('start', start_conversation)],
           states={
               'SPEAKER': [
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
        lecture=lecture,
        answered=False,
    )
    return questions


def decline_question(n):
    if n % 100 == 1:
        return 'не отвеченный вопрос'
    elif n % 10 in [2, 3, 4] and n % 100 not in [12, 13, 14]:
        return 'не отвеченных вопроса'
    else:
        return 'не отвеченных вопросов'
