# PythonMeetup
Данный репозиторий представляет собой удобный инструмент для управления и планированию мероприятий.
Содержит в себе веб админку, а так же бота, через который можно отправлять вопрсы спикерам, а лектором соотвесвенно их просматривать и отвечать.

### Как установить
Для запуска сайта вам понадобится Python третьей версии.

Скачайте код с GitHub. Установите зависимости:

```sh
pip install -r requirements.txt
```

Создайте базу данных SQLite

```sh
python3 manage.py makemigrations
python3 manage.py migrate
```
Создайте суперпользователя
```sh
python3 manage.py createsuperuser
```

Перед установкой создайте файл **.env** вида:
```properties
TG_SPEAKER_TOKEN=YOUR_TG_TOKEN
TG_LISTENER_TOKEN=YOUR_TG_TOKEN
PAYMENTS_TOKEN=PAYMENTS_TOKEN
```
- Токен для Телеграм бота вы можете получить https://telegram.me/BotFather Чат ID можно узнать в свойствах канала
- Не забудьте прописать команду `/setinline.`а так же задайте описание бота через `/setdescription`
- Подключите оплату в настройках бота через BotFather

### Как запустить
Для запуска бота спикера используйте команду
```sh
python manage.py runspeakerbot
```
Для запуска бота слушателя используйте команду
```sh
python manage.py run_meetup_bot
```

Для запуска админки используйте команду
```sh
python manage.py runserver
```

### Вспомогательные интрументы
В репозитории присутсвует скрипт заполнения БД тестовыми данными. Для его запуска воспользуйтесь командой
```sh
python add_test_data_in_bd.py
```
