import vk_api
import time
import datetime as dt
from scheduler import Scheduler
from vk_api.longpoll import VkLongPoll
from vk_api.utils import get_random_id
from parser import Parser, Course
from json_classes import JsonConfig


class Notifications:
    def __init__(self, login, password, token, json_config: JsonConfig):
        self.__parser = Parser(login=login, password=password, json_config=json_config)
        self.__json_config = json_config
        self.__vk_session = vk_api.VkApi(token=token)
        self.__session_api = self.__vk_session.get_api()
        self.__longpoll = VkLongPoll(self.__vk_session)

    def __handler(self):
        courses_data: list[Course] = self.__parser.parse()
        message_text = ""
        for course in courses_data:
            message_text += f"{course.name}\n"
            for lesson in course.lessons:
                message_text += f"➥ {lesson.name}. Работ: {lesson.count}\n"
            message_text += "\n"

        for peer_id in self.__json_config.peer_ids:
            try:
                self.__session_api.messages.send(peer_id=peer_id, message=message_text, random_id=get_random_id())
            except Exception as ex:
                print(ex)

    def start(self):
        schedule = Scheduler(tzinfo=dt.timezone.utc)
        tz_moscow = dt.timezone(dt.timedelta(hours=3))
        for hour in [0, 8, 12, 15, 18, 21]:
            schedule.daily(dt.time(hour=hour, tzinfo=tz_moscow), self.__handler)
        while True:
            schedule.exec_jobs()
            time.sleep(1)
