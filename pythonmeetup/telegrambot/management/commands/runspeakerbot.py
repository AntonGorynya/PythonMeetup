from django.core.management.base import BaseCommand
from pythonmeetup import settings
from ...models import Listener, Question, Lecture, Event
from telegram.error import BadRequest
import datetime
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    Update,
    LabeledPrice
)
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    CallbackContext,
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

        def start(update, context):
            query = update.callback_query
            if update.message:
                username = update.message.from_user.username
            else:
                username = query.message.chat['username']
            listener = Listener.objects.get(nickname=username)
            context.user_data['user'] = username
            context.user_data['status'] = "FIRST"

            keyboard = [
                [
                    InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')
                ],
                [
                    InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')
                ]
            ]
            if listener.isspeaker:
                keyboard.append(
                    [
                        InlineKeyboardButton("Посмотреть вопросы", callback_data='to_speaker')
                    ]
                )
            reply_markup = InlineKeyboardMarkup(keyboard)
            message_text = f"Добро пожаловать {context.user_data['user']}!\n" \
                           f"Мы рады Вас приветствовать в сервисе PythonMeetup. \n"
            if update.message:
                msg = update.message.reply_text(
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            else:
                msg = edit_message_if_new(query, message_text, '', reply_markup)

            context.user_data['msg'] = msg.message_id
            return 'FIRST'

        def get_schedule_events(update, context):
            context.user_data['status'] = 'FIRST'
            date = datetime.date.today()
            event_schedule_list = []
            lecture_data = Lecture.objects.all()
            for i, item in enumerate(lecture_data, 1):
                if item.date == date:
                    if len(event_schedule_list) == 0:
                        event_schedule_list.append(f'\nМероприятие: {item.event} \nРассписание на {date} \n')
                        event_schedule_list.append(
                            f'{len(event_schedule_list)}. {item.topic}, Докладчик: {str(item.speaker).split(" ")[0]},'
                            f' Время проведения: {item.start_time} - {item.end_time} \n')
                    else:
                        event_schedule_list.append(
                            f'{len(event_schedule_list)}. {item.topic}, Докладчик: {str(item.speaker).split(" ")[0]},'
                            f' Время проведения: {item.start_time} - {item.end_time} \n')
                if len(lecture_data) == i:
                    if len(event_schedule_list) == 0:
                        event_schedule_list.append(f'***\nРассписание на {date} отсутствует!\n\n****')

            event_schedule = ' '.join(map(str, event_schedule_list))

            query = update.callback_query
            query.answer()
            keyboard = [
                [
                    InlineKeyboardButton("На главную", callback_data='to_start'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text=f"Мы рады Вас приветствовать в сервисе PythonMeetup. \n {event_schedule}\n",
                reply_markup=reply_markup
            )
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
                text=f"Мы рады Вас приветствовать в сервисе PythonMeetup.\nНапишите Ваш вопрос по текущему докладу:\n", reply_markup=reply_markup
            )

            return 'SECOND'

        def echo(update: Update, context: CallbackContext) -> None:
            question = update.message.text.strip()
            context.bot.delete_message(chat_id=update.effective_chat.id,
                                       message_id=update.message.message_id)

            if context.user_data['status'] == 'SECOND':
                try:
                    create_questions(update.message.text)
                    context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['msg'],
                                                  text=f'***\n{context.user_data["user"]}, Ваш вопрос:\n" {update.message.text} "\n ОТПРАВЛЕН!\n\n***')
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
            start(update, context)


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

        def start_speaker_conversation(update, context):
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
                        InlineKeyboardButton("Перейти к вопросам", callback_data='to_show_questions'),
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
            edit_message_if_new(query, message_text, previous_text, reply_markup)

            # if message_text != previous_text:
            #     if update.message:
            #         update.message.reply_text(
            #             text=message_text,
            #             reply_markup=reply_markup,
            #             parse_mode=ParseMode.HTML
            #         )
            #     else:
            #         edit_message_if_new(query, message_text, previous_text, reply_markup)

            return 'SPEAKER'

        def show_question(update, context):
            query = update.callback_query
            previous_text = query.message.text
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
                message_text = f"Вопрос от пользователя @{question.listener.nickname}:\n {question.text}"
            else:
                message_text = f"Вы ответили на все вопросы"

            edit_message_if_new(query, message_text, previous_text, reply_markup)
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
           entry_points=[CommandHandler('start', start)],
           states={
               'SPEAKER': [
                   CallbackQueryHandler(end_conversation, pattern='to_end_lecture'),
                   CallbackQueryHandler(show_question, pattern='to_show_questions|mark|1|-1'),
                   CallbackQueryHandler(start_speaker_conversation, pattern='to_start'),
               ],
               'FIRST': [
                   CallbackQueryHandler(get_schedule_events, pattern='event_plan'),
                   CallbackQueryHandler(get_question, pattern='to_question'),
                   CallbackQueryHandler(start_speaker_conversation, pattern='to_speaker')
               ],
               'SECOND': [
                   CallbackQueryHandler(start, pattern='to_start')
               ],
           },
           fallbacks=[CommandHandler('cancel', cancel)]
        )
        echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
        dispatcher.add_handler(echo_handler)

        dispatcher.add_handler(conv_handler)
        dispatcher.add_handler(CommandHandler('start', start))
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


def edit_message_if_new(query, message_text, previous_text, reply_markup):
    if message_text != previous_text:
        msg = query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return msg
