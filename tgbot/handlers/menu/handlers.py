import datetime
import os
import pytz
import logging
from django.utils import timezone
from django.db.models import Q
from typing import Optional

from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.utils import local_datetime
from tgbot.handlers.menu import manage_data, static_text
from tgbot.handlers.utils.info import extract_user_data_from_update
from tgbot.handlers.utils.files import load_yaml
from users.models import User, Booking
from tgbot.validation import password_validation, username_validation
from tgbot.handlers.menu.keyboards import make_keyboard


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')
answers = load_yaml('tgbot/handlers/menu/static_text.yml')
config = load_yaml('tgbot/config.yml')
time_zone = pytz.timezone('Europe/Moscow')



# # # При нажатии пользователем команды /start бот обращается к базе данных для проверки введеного пароля и
# Фамилии и имени пользователя. Если данные введены, то бот выводит меню с выбором комнат. Если нет, то бот запросит
# пароль. #TODO - вынести пароль в переменную окружения
def command_start(update: Update, context: CallbackContext) -> None:
    logger.info("Start to new booking")
    manage_data = load_yaml('tgbot/handlers/menu/manage_data.yml')
    u, created = User.get_user_and_created(update, context)
    data = extract_user_data_from_update(update)

    entered_password = User.get_is_password(data.get("user_id"))
    is_fullname = User.get_is_fullname(data.get("user_id"))

    if not entered_password:
        update.message.reply_text(
            text=answers.get("start_created")
        )
    elif entered_password and not is_fullname:
        update.message.reply_text(
            text=answers.get("input_fullname"))
    else:

        return update.message.reply_text(
            text=answers.get("user_exist"),
            reply_markup=make_keyboard(manage_data.get('main'))
        )

# # # Проверка наличия введенного пароля и фамилии/имени пользователя. В случае, отсутствия, последовательно
# запрашиваем данные через пользовательский ввод. В случае, когда и пароль, и фамилия/имя будут введены,
# пользователь увидит кнопки с названиями переговорных
def main_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    data = extract_user_data_from_update(update)
    is_auth = User.get_is_password(data.get("user_id"))
    fullname_is_set = User.get_is_fullname(username_or_user_id=data.get("user_id"))

    message_text = update.message.text

    if not is_auth and password_validation and message_text == os.getenv("USER_PASSWORD"):
        User.update_is_password(user_id)
        update.message.reply_text(
            text=answers.get("input_fullname"))

    elif is_auth and not fullname_is_set and username_validation(message_text):
        User.update_is_fullname(user_id, fullname=message_text)
        manage_data = load_yaml('tgbot/handlers/menu/manage_data.yml')

        return update.message.reply_text(
            text=answers.get("user_exist").format(first_name=message_text),
            reply_markup=make_keyboard(manage_data.get('main'))
        )
    else:
        logger.info("Incorrect data in password input or in fullname input")
        return update.message.reply_text(
            text=answers.get("incorrect_format"))


class Menu:

    def __init__(self, path_to_file):
        self.keyboard = load_yaml(path_to_file)
        self.DAYS_FOR_SHOW = 31
        self.booking_info = {}
        self.dates = [(datetime.date.today() + datetime.timedelta(days=i)).strftime('%d.%m') for i in range(self.DAYS_FOR_SHOW)]
        # self.page_number = 0
        # self.DAYS_PER_PAGE = 7
        # self.pages = [self.dates[i:i + self.DAYS_PER_PAGE] for i in range(0, len(self.dates), self.DAYS_PER_PAGE)]

    def generate_1(self, update: Update, context: CallbackContext, text, keyboard=None, parse_mode=ParseMode.HTML) -> None:
        user_id = extract_user_data_from_update(update).get('user_id')
        try:
            context.bot.edit_message_text(
                text=text,
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id,
                parse_mode=parse_mode,
                reply_markup=keyboard
            )
        except Exception as error:
            logger.error(error)
            print("ERROR: ", error)

    def generate(self, update: Update, context: CallbackContext, text, keyboard=None, parse_mode=ParseMode.HTML) -> None:
        user_id = extract_user_data_from_update(update).get('user_id')

        try:
            context.bot.edit_message_text(
                text=text,
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id,
                parse_mode=parse_mode,
                reply_markup=keyboard
            )
        except Exception as error:
            logger.error(error)
            print("ERROR: ", error)

    def main(self, update: Update, context: CallbackContext) -> None:
        self.generate(update, context, answers.get("main_menu"),
                      make_keyboard(self.keyboard.get('main'))
                      )

    # @classmethod
    # def local_datetime(self) -> Optional[datetime.datetime]:
    #     local_date = datetime.datetime.now(time_zone)
    #     return local_date

    def room_menu(self, update: Update, context: CallbackContext) -> None:
        # # # Получаем айди пользователя, отправившего колбек(нажатие на кнопку с названием комнаты),
        #  и ищем его в базе данных.
        user_id = update.callback_query.from_user.id
        user_from_db = User.get_is_fullname(user_id)
        # # # Получаем информацию о комнате(колбек имеет название комнаты)
        query = update.callback_query
        data = query.data
        # # # Наполняем словарь данными (Имя Фамилия, название комнаты
        self.booking_info.clear()
        self.booking_info.update({'user': user_from_db, 'room': data, 'user_id': user_id})
        # # # Отправляем сообщение и генерируем новые кнопки с колбеками
        self.generate(update, context, answers.get("choose_day_or_see_time"),
                      make_keyboard(self.keyboard.get('choosed_room')))

    def choose_monthday(self, update: Update, context: CallbackContext) -> None:
        # # # Формирование кнопок для получения даты(пример 21.03). Отображается месяц, без учета выходных дней
        # Создаем динамический колбек для перехода к след. методу
        data = {
            f"choose_{day}": {
                "callback_data": self.dates[day],
                "name": f"{self.dates[day]}:"
            } for day in range(self.DAYS_FOR_SHOW)
        }
        for day in data:
            data[day]["name"] = (local_datetime().today() + datetime.timedelta(days=int(day.split("_")[1]))).strftime(
                '%d.%m')

        # # # Генерация сообщения с текстом и кнопками
        self.generate(update, context, answers.get("choose_date"),
                      make_keyboard(data, n_cols=3)
                      )

    def choose_hours(self, update: Update, context: CallbackContext) -> None:
        # # # Получение значения из кнопки(колбека)
        query = update.callback_query
        query_data = query.data
        message = ''

        # # # Получаем дату для записи в бд. Используем, для выведения данных об уже известных бронированиях
        date_for_search = str(local_datetime().year) + '-' + query_data.split('.')[1] + '-' + query_data.split('.')[0]
        # # # Обновление информации в словаре даты бронирования и окончания(в след. методах будет добавляться время)
        self.booking_info.update({'start_date': date_for_search, 'end_date': date_for_search})
        date_for_message = query_data.split('.')[0] + '-' + query_data.split('.')[1] + '-' + str(local_datetime().year)
        self.booking_info.update({'date_for_message': date_for_message, 'end_date_for_message': date_for_message})
        logger.debug(self.booking_info)

        # Проверяем, существует ли бронирование в указанной комнате
        info_from_db = Booking.get_booking_by_day(self.booking_info.get('room'), self.booking_info.get('start_date'))
        if info_from_db:
            message += answers.get("active_booking_on_choosen_day") + '\n\n' + info_from_db + '\n\n' \
                      + answers.get("choose_hours_text")
        else:
            message += answers.get("choose_hours_text")

        # # # Формирование кнопок для получения часов у времени(пример 10:). Начиная с 8 часов утра,
        # заканчивая 20 вечера.
        # Создаем динамический колбек для перехода к след. методу
        data = {
            f"choose_{hour}": {
                "callback_data": str(hour) + ":",
                "name": f"{hour}:"
            } for hour in range(8, 21)
        }

        # # # Генерация сообщения с текстом и кнопками
        self.generate(update, context, message,
                      make_keyboard(data))

    def choose_minutes(self, update: Update, context: CallbackContext) -> None:
        # # # Получение значения из кнопки(колбека)
        query = update.callback_query
        query_data = query.data
        message = ''
        self.booking_info.update({'start_time': query_data})
        logger.debug(self.booking_info)
        # # # Повторяем алгоритм выше. Для удобства пользователя при бронирования переговорной
        info_from_db = Booking.get_booking_by_day(self.booking_info.get('room_name'), self.booking_info.get('date_for_search'))
        if info_from_db:
            message += answers.get("active_booking_on_choosen_day") + '\n\n' + info_from_db + '\n\n' \
                       + answers.get("choose_hours_text")
        else:
            message += answers.get("choose_hours_text")

        # # # Формирование кнопок для получения минут у времени(пример ..:10). Начиная от 10 минут, заканчивая 50.
        # Колбек для перехода к след. методу
        data = {
            f"choose_{str(minutes).zfill(2)}": {
                "callback_data": ":" + str(minutes).zfill(2),
                "name": f":{str(minutes).zfill(2)}"
            } for minutes in range(0, 51, 10)
        }

        # # # Генерация сообщения с текстом и кнопками
        self.generate(update, context, answers.get("choose_minutes_text"),
                      make_keyboard(data))

    def choose_minutes_for_booking(self, update: Update, context: CallbackContext) -> None:
        # # # Получение значения из кнопки(колбека)
        query = update.callback_query
        query_data = query.data.replace(":", "")
        message = ''

        # # # Получаем и актуализируем в словаре нужное время + время с датой.
        time = self.booking_info.get('start_time') + query_data
        new_datetime = self.booking_info.get('start_date').replace(".", "-") + ' ' + time

        # Формируем дату для отображения в сообщении (по запросу коллег).
        datetime_for_message = self.booking_info.get('date_for_message').replace("-", ".") + ' ' + time

        # Обновляем словарь бронирования
        self.booking_info.update({'start_time': time})
        self.booking_info.update({'start_date': new_datetime, 'date_for_message': datetime_for_message})
        logger.debug(self.booking_info)
        info_from_db = Booking.get_booking_by_day(self.booking_info.get('room_name'),
                                                  self.booking_info.get('date_for_search'))
        if info_from_db:
            message += answers.get("active_booking_on_choosen_day") + '\n\n' + info_from_db + '\n\n' \
                       + answers.get("choose_hours_text")
        else:
            message += answers.get("choose_hours_text")

        # # # Формирование кнопок для получения минут у времени(пример ..:10). Начиная от 10 минут, заканчивая 50.
        # Колбек для перехода к след. методу
        data = {
            f"choose_{minutes}": {
                "callback_data": str(minutes),
                "name": f"{minutes} минут"
            } for minutes in range(30, 241, 30)
        }
        self.generate(update, context, answers.get("choose_minutes_for_booking_text"),
                      make_keyboard(data))

    def confirm_booking(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query_data = query.data
        time_obj = datetime.datetime.strptime(self.booking_info.get('start_time'), '%H:%M')
        new_time_obj = time_obj + datetime.timedelta(minutes=int(query_data))

        # Преобразуем объект datetime обратно в строку времени
        new_time_str = self.booking_info.get('end_date').replace(".", "-")\
                       + ' ' + new_time_obj.strftime('%H:%M')

        # Формируем дату для отображения в сообщении (по запросу коллег).
        new_time_str_for_message = self.booking_info.get('end_date_for_message').replace("-", ".")\
                       + ' ' + new_time_obj.strftime('%H:%M')

        # Обновляем словарь бронирования
        self.booking_info.update({'end_date': new_time_str, 'end_date_for_message': new_time_str_for_message})
        logger.debug(self.booking_info)
        message = answers.get("info_about_booking").format(user=self.booking_info.get('user'),
                                                room=self.booking_info.get('room'),
                                                start_date=self.booking_info.get('date_for_message'),
                                                end_date=self.booking_info.get('end_date_for_message'))


        data = {
            f"confirm": {
                "callback_data": manage_data.CONFIRM,
                "name": answers.get("confirm")
            }
        }
        self.generate(update, context, message,
                      make_keyboard(data))


    # # # Подтверждение информации о бронировании. Выводится в конце бронирования
    def confirm_info(self, update: Update, context: CallbackContext) -> None:
        logger.info(self.booking_info)

        start_datetime = datetime.datetime.strptime(self.booking_info.get('start_date')
                                                    , config.get("date_format"))

        end_datetime = datetime.datetime.strptime(
                            self.booking_info.get('end_date'),
                            config.get("date_format")
                            ) - datetime.timedelta(minutes=1)

        room_name = self.booking_info.get('room')

        # Проверяем, существует ли бронирование в указанной комнате
        is_created_rooms = Booking.objects.filter(room_name=room_name)

        if is_created_rooms.exists():
            # Проверяем, есть ли пересекающиеся бронирования
            is_created = Booking.objects.filter(
                Q(room_name=room_name) & (

                        Q(start_datetime__range=(start_datetime, end_datetime))
                        | Q(end_datetime__range=(start_datetime, end_datetime))
                        | Q(start_datetime__lt=end_datetime) & Q(end_datetime__gt=start_datetime)
                )
            )

            if is_created.exists():
                message = answers.get("busy_room").format(room_name=self.booking_info.get('room'))
            else:

                Booking.objects.create(room_name=self.booking_info.get('room'),
                                       start_datetime=start_datetime,
                                       end_datetime=end_datetime,
                                       user=self.booking_info.get('user'))

                message = answers.get("success_answer")
                message_about_booking = answers.get("info_from_db").format(room_name=self.booking_info.get('room'),
                                                                           start_datetime=self.booking_info.get('date_for_message'),
                                                                           end_datetime=self.booking_info.get('end_date_for_message'),
                                                                           user=self.booking_info.get('user'))
                context.bot.send_message(chat_id=self.booking_info.get('user_id'), text=message_about_booking)

        else:
            Booking.objects.create(room_name=self.booking_info.get('room'),
                                   start_datetime=start_datetime,
                                   end_datetime=end_datetime,
                                   user=self.booking_info.get('user'))
            message = answers.get("success_answer")
            message_about_booking = answers.get("info_from_db").format(room_name=self.booking_info.get('room'),
                                                                       start_datetime=self.booking_info.get(
                                                                           'date_for_message'),
                                                                       end_datetime=self.booking_info.get(
                                                                           'end_date_for_message'),
                                                                       user=self.booking_info.get('user'))
            context.bot.send_message(chat_id=self.booking_info.get('user_id'), text=message_about_booking)

        self.generate(update, context, message,
                      make_keyboard(self.keyboard.get('main')))

    def active_booking(self, update: Update, context: CallbackContext) -> None:
        view_active_booking = Booking.get_booking_by_roomname(room_name=self.booking_info.get('room'))
        message = ''
        if view_active_booking:
            message += view_active_booking + "\n\n" + answers.get("choose_room")
        else:
            message += answers.get("not_active_booking").format(room_name=self.booking_info.get('room')) + "\n\n" + answers.get("choose_room")
        self.generate(update, context, message,
                      make_keyboard(self.keyboard.get('main')))

    def delete_booking_info(self, update: Update, context: CallbackContext) -> None:
        view_active_booking = Booking.get_booking_with_id(user=self.booking_info.get('user'), room_name=self.booking_info.get('room'))
        ids = Booking.get_booking_id(user=self.booking_info.get('user'), room_name=self.booking_info.get('room'))
        message = ''
        data = {}
        if view_active_booking and ids:
            for item in ids:
                data.update({
                    f"choose_{item}": {
                        "callback_data": f"Номер: {item}",
                        "name": f"Номер: {item}"
                    }
                })
            message += view_active_booking + "\n\n" + answers.get("choose_id_for_deleting").format(room_name=self.booking_info.get('room'))
            self.generate(update, context, message,
                          make_keyboard(data))
        else:
            message += answers.get("not_active_booking").format(room_name=self.booking_info.get('room')) + "\n\n" + answers.get("choose_room")
            self.generate(update, context, message,
                          make_keyboard((self.keyboard.get('main'))))

    def delete_booking(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query_data = query.data.split(":")
        Booking.delete_booking_by_id(query_data[1])

        self.generate(update, context, answers.get("success_deleting"),
                      make_keyboard(self.keyboard.get('main')))



    # # # Метод для отслеживания кнопок вперед назад при выборе дат. Не используется, реализован вывод целого месяца
    # def handle_page(self, update: Update, context: CallbackContext) -> None:
    #     query = update.callback_query
    #     data = query.data
    #     # If the 'Next' button is pressed, send the next page of dates
    #     if data == 'next':
    #         if self.page_number < len(self.pages) - 1:
    #             self.page_number += 1
    #             reply_markup = generate_markup(self.pages[self.page_number])
    #             query.edit_message_reply_markup(reply_markup=reply_markup)
    #         else:
    #             query.answer()
    #     elif data == 'back':
    #         # If the 'Back' button is pressed, send the previous page of dates
    #         if self.page_number > 0:
    #             self.page_number -= 1
    #             reply_markup = generate_markup(self.pages[self.page_number])
    #             query.edit_message_reply_markup(reply_markup=reply_markup)
    #         else:
    #             query.answer()
