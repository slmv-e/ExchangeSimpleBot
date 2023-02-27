from vkbottle.bot import Bot, Message
from vkbottle.dispatch.rules import ABCRule
from asyncio import run
from threading import Thread
from environs import Env
from typing import Tuple
from json_classes import JsonWorker
from notifications import Notifications

env = Env()
env.read_env(".env")
token = env.str("TOKEN")
bot = Bot(token=token)

json_worker = JsonWorker()
json_config = json_worker.read()


class AdminRule(ABCRule[Message]):
    def __init__(self, rule: bool):
        self.rule = rule

    async def check(self, event: Message) -> bool:
        return True if not self.rule else True if (await event.get_user()).id in json_config.admin_ids else False


bot.labeler.custom_rules["admin_only"] = AdminRule


@bot.on.message(command=("smp_help", 0), admin_only=True)
async def smp_help(message: Message):
    await message.answer("Команды:\n"
                         "/smp_add_this_chat - Добавляет чат\n"
                         "/smp_add_course_id <id> - Добавляет Course ID\n"
                         "/smp_remove_course_id <id> - Удаляет Course ID")


@bot.on.message(command=("smp_add_this_chat", 0), admin_only=True)
async def add_this_chat(message: Message):
    peer_id = message.peer_id
    if peer_id not in json_config.peer_ids:
        json_config.peer_ids.append(peer_id)
        json_worker.write(json_config)

        await message.answer("Этот чат успешно добавлен")
    else:
        await message.answer("Этот чат уже есть в списке")


@bot.on.message(command=("smp_add_course_id", 1), admin_only=True)
async def add_course_id(message: Message, args: Tuple[str]):
    try:
        course_id = int(args[0])
    except TypeError:
        await message.answer("Нужно указать число")
    else:
        if course_id not in json_config.course_ids:
            json_config.course_ids.append(course_id)
            json_worker.write(json_config)

            await message.answer("Course ID успешно добавлен")
        else:
            await message.answer("Данный Course ID уже есть в списке")


@bot.on.message(command=("smp_remove_course_id", 1), admin_only=True)
async def remove_course_id(message: Message, args: Tuple[str]):
    try:
        course_id = int(args[0])
    except TypeError:
        await message.answer("Нужно указать число")
    else:
        if course_id in json_config.course_ids:
            json_config.course_ids.remove(course_id)
            json_worker.write(json_config)

            await message.answer("Course ID успешно удален")
        else:
            await message.answer("Данного Course ID нет в списке")


def main():
    login = env.str("LOGIN")
    password = env.str("PASSWORD")

    notifications_app = Notifications(login, password, token, json_config)

    notifications_process = Thread(target=notifications_app.start)
    bot_process = Thread(target=run, args=(bot.run_polling(),))

    notifications_process.start()
    bot_process.start()

    notifications_process.join()
    bot_process.join()


if __name__ == "__main__":
    main()
