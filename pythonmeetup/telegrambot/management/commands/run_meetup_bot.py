from environs import Env
import datetime
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
    TypeHandler
)

# Ведение журнала логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update, _):
    """Вызывается по команде `/start`."""
    # Получаем пользователя, который запустил команду `/start`
    user = update.message.from_user
    logger.info("Пользователь %s начал разговор", user.first_name)

    keyboard = [
        [InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')],
        [InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с текстом и добавленной клавиатурой `reply_markup`
    update.message.reply_text(
        text="Мы рады Вас приветствовать в сервисе PythonMeetup \n"
             "Наша площадка проводит онлайн конференции", reply_markup=reply_markup
    )
    # Сообщаем `ConversationHandler`, что сейчас состояние `FIRST`
    return 'FIRST'


def start_over(update, _):
    """Тот же текст и клавиатура, что и при `/start`, но не как новое сообщение"""
    # Получаем `CallbackQuery` из обновления `update`
    query = update.callback_query
    # На запросы обратного вызова необходимо ответить,
    # даже если уведомление для пользователя не требуется.
    # В противном случае у некоторых клиентов могут возникнуть проблемы.
    query.answer()
    keyboard = [
        [InlineKeyboardButton("Посмотреть план мероприятия", callback_data='event_plan')],
        [InlineKeyboardButton("Задать вопрос по текущему докладу", callback_data='to_question')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отредактируем сообщение, вызвавшее обратный вызов.
    # Это создает ощущение интерактивного меню.
    query.edit_message_text(
        text="Мы рады Вас приветствовать в сервисе PythonMeetup \n"
             "Наша площадка проводит онлайн конференции", reply_markup=reply_markup)
    return 'FIRST'


def get_schedule_events(update, _):
    """Показ нового выбора кнопок"""
    query = update.callback_query
    query.answer()
    keyboard = [
        [
            InlineKeyboardButton("На главную", callback_data='to_start'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="Выводим таблицу или данные с расписание по мероприятию (Выводить за один день или за все мероприятие если оно длится например 2 дня)",
        reply_markup=reply_markup
    )
    return 'SECOND'


def get_question(update, _):
    """Показ нового выбора кнопок"""
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
    updater.dispatcher.add_handler(TypeHandler(Update, echo))
    return 'SECOND'


def end(update, _):
    """Возвращает `ConversationHandler.END`, который говорит
    `ConversationHandler` что разговор окончен"""
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="ДО скорой встречи!")
    return ConversationHandler.END


def echo(update: Update, context: CallbackContext) -> None:
    text = json.dumps(update.to_dict(), indent=2)

    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


# После ввода вопроса вывести - Ваш вопрос отправлен, в ближайшее время докладчик Вам ответит.
# И наверное переходим на главную.

if __name__ == '__main__':
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    date = datetime.date.today()
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

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

    # Добавляем `ConversationHandler` в диспетчер, который
    # будет использоваться для обработки обновлений
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
    print('Started')
