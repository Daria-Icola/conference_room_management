from __future__ import annotations
from typing import Union, Optional, Tuple
import logging
import datetime
import pytz

from django.db import models
from django.db.models import QuerySet, Manager
from django.utils import timezone
from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.utils.info import extract_user_data_from_update
from tgbot.utils import time_zone, local_datetime
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager
from tgbot.handlers.utils.files import load_yaml

answers = load_yaml('tgbot/handlers/menu/static_text.yml')
config = load_yaml('tgbot/config.yml')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main')


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    fullname = models.CharField(max_length=256)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    is_logging = models.BooleanField(default=False)
    is_password = models.BooleanField(default=False)
    is_blocked_bot = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    def __str__(self):
        return f'@{self.username}, {self.is_password}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)
        # auth = cls.objects.update_or_create(is_password=data["is_password"], defaults=data)
        # print("AUTH: ", auth)
        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()
        return u, created

    @classmethod
    def get(cls, username_or_user_id: Union[str, int], key, filter=None) -> Optional[User]:
        all = cls.objects.all().values()
        for item in all:
            if item.get("user_id") == username_or_user_id or item.get("username") == username_or_user_id:
                return item.get(key)


    @classmethod
    def get_is_password(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        all = cls.objects.all().values()
        for item in all:
            if item.get("user_id") == username_or_user_id or item.get("username") == username_or_user_id:


                return item.get("is_password")

    @classmethod
    def get_is_fullname(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        all = cls.objects.all().values()
        for item in all:
            if item.get("user_id") == username_or_user_id or item.get("username") == username_or_user_id:
                return item.get("fullname")



    @classmethod
    def update_is_password(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        all = cls.objects.all().values()
        for item in all:
            if item.get("user_id") == username_or_user_id or item.get("username") == username_or_user_id:
                user_id = item.get("user_id")
                return cls.objects.filter(user_id=user_id).update(is_password=True)

    @classmethod
    def update_is_fullname(cls, username_or_user_id: Union[str, int], fullname) -> Optional[User]:
        all = cls.objects.all().values()
        for item in all:
            if item.get("user_id") == username_or_user_id or item.get("username") == username_or_user_id:
                user_id = item.get("user_id")
                return cls.objects.filter(user_id=user_id).update(fullname=fullname)




    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)

        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()
    admins = AdminUserManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime(config.get('date_format'))}"


class Rooms(models.Model):
    room_id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=64)
    objects = GetOrNoneManager()

    def __str__(self):
        return f"{self.room_id}: {self.room_name}"

    @classmethod
    def insert_table(cls):
        objs = [
            Rooms(room_id=1, room_name="Кандинский"),
            Rooms(room_id=2, room_name="Пименов"),
            Rooms(room_id=3, room_name="Родченко 30"),
            Rooms(room_id=4, room_name="Любовь Попова"),
        ]

        cls.objects.bulk_create(objs)


class Booking(CreateTracker):
    room_name = models.CharField(max_length=256) #ForeignKey(Rooms, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    user = models.CharField(max_length=256)   #ForeignKey(TgUser, null=True, blank=True, on_delete=models.CASCADE)
    objects = GetOrNoneManager()

    def __str__(self):
        return f"{self.room_name}: {self.user} - {self.start_datetime} - {self.end_datetime}"



    @classmethod
    def get_booking_by_roomname(cls, room_name: str) -> Optional[str]:
        try:
            bookings = cls.objects.filter(room_name=room_name, start_datetime__gte=local_datetime().astimezone(time_zone).date()).order_by('start_datetime')
            if not bookings:
                return None
            data = []

            for booking in bookings:

                data.append(answers.get("info_from_db").format(room_name=booking.room_name,
                                                               user=booking.user,
                                                               start_datetime=booking.start_datetime.astimezone(time_zone).strftime(config.get("date_format_for_message")),
                                                               end_datetime=(booking.end_datetime + datetime.timedelta(minutes=1)).astimezone(time_zone).strftime(config.get("date_format_for_message"))))

            return "\n".join(data)
        except Exception as error:
            logger.error(error)


    @classmethod
    def get_booking_by_day(cls, room_name: str, date: str) -> Optional[str]:
        try:
            if date:
                arr_date = date.split('-')
                start_of_day = timezone.make_aware(datetime.datetime(year=int(arr_date[0]), month=int(arr_date[1]), day=int(arr_date[2])), timezone=pytz.timezone('Europe/Moscow'))
                end_of_day = start_of_day + datetime.timedelta(days=1)

                bookings = cls.objects.filter(room_name=room_name,
                                              start_datetime__range=(start_of_day.strftime(config.get("date_format")),
                                                                     end_of_day.strftime(config.get("date_format"))))
                if not bookings:
                    return None
                data = []
                for booking in bookings:
                    data.append(answers.get("info_from_db").format(room_name=booking.room_name,
                                                                   user=booking.user,
                                                                   start_datetime=booking.start_datetime.astimezone(time_zone).strftime(
                                                                       config.get("date_format_for_message")),
                                                                   end_datetime=(booking.end_datetime + datetime.timedelta(minutes=1)).astimezone(time_zone).strftime(
                                                                       config.get("date_format_for_message"))))

                return "\n".join(data)
            else:
                pass
        except Exception as error:
            logger.error(error)

    @classmethod
    def get_booking_with_id(cls, user: str, room_name: str) -> Optional[str]:
        try:
            bookings = cls.objects.filter(user=user, room_name=room_name,  start_datetime__gte=local_datetime().astimezone(time_zone).date()).order_by('start_datetime')
            if not bookings:
                return None
            data = []

            for booking in bookings:
                data.append(answers.get("info_from_db_with_id").format(id=booking.id,
                                                               room_name=booking.room_name,
                                                               user=booking.user,
                                                               start_datetime=booking.start_datetime.astimezone(time_zone).strftime(
                                                                   config.get("date_format_for_message")),
                                                               end_datetime=(booking.end_datetime + datetime.timedelta(minutes=1)).astimezone(time_zone).strftime(
                                                                   config.get("date_format_for_message"))))

            return "\n".join(data)
        except Exception as error:
            logger.error(error)

    @classmethod
    def get_booking_id(cls, user: str, room_name: str):
        try:
            bookings = cls.objects.filter(user=user, room_name=room_name, start_datetime__gte=local_datetime().astimezone(time_zone).date()).order_by('start_datetime')
            if not bookings:
                return None
            data = []
            for booking in bookings:
                data.append(booking.id)
            return data
        except Exception as error:
            logger.error(error)



    @classmethod
    def delete_booking_by_id(cls, id: str) -> Optional[str]:
        try:
            booking = cls.objects.filter(id=id)
            if booking:
                return booking.delete()
            else:
                return
        except Exception as error:
            logger.error(error)
