import requests
from bs4 import BeautifulSoup
from typing import NamedTuple
from json_classes import JsonConfig


class Lesson(NamedTuple):
    name: str
    count: int


class Course(NamedTuple):
    name: str
    id: int
    lessons: list[Lesson]


class Authorization:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }

    def _auth(self, session):
        url = "https://api.100points.ru/login"

        data = {
            'email': self.login,
            'password': self.password
        }

        session.post(url, data=data, headers=self.headers)  # response


class Parser(Authorization):
    def __init__(self, login: str, password: str, json_config: JsonConfig):
        super().__init__(login, password)
        self.json_config = json_config

    def parse(self) -> list[Course]:
        output: list[Course] = []

        with requests.Session() as session:
            self._auth(session)

            for course_id in self.json_config.course_ids:
                url = f"https://api.100points.ru/exchange/index?email=&name=&course_id={course_id}"
                with session.get(url=url, headers=self.headers) as resp:
                    course_soup = BeautifulSoup(resp.text, "html.parser")

                course_name = course_soup.select_one("#course_id > option[selected]").text.replace("\n", "").strip()
                course_lessons = []

                module_ids = [module['value'] for module in course_soup.select("#module_id > option")]
                for module_id in module_ids:
                    if not module_id:
                        continue

                    url = f"https://api.100points.ru/exchange/index?email=&name=&course_id={course_id}&module_id={module_id}"
                    with session.get(url=url, headers=self.headers) as resp:
                        module_soup = BeautifulSoup(resp.text, "html.parser")

                    lesson_ids = [lesson['value'] for lesson in module_soup.select("#lesson_id > option")]
                    for lesson_id in lesson_ids:
                        if not lesson_id:
                            continue

                        url = f"https://api.100points.ru/exchange/index?email=&name=&course_id={course_id}&module_id={module_id}&lesson_id={lesson_id}"
                        with session.get(url=url, headers=self.headers) as resp:
                            lesson_soup = BeautifulSoup(resp.text, "html.parser")

                        lesson_name = lesson_soup.select_one("#lesson_id > option[selected]").text.replace("\n", "").strip()
                        try:
                            works_count = int(lesson_soup.find('div', id='example2_info').text.split()[-1])
                        except AttributeError:
                            try:
                                works_count = len(lesson_soup.find('tbody').find_all('tr'))
                            except AttributeError:
                                works_count = 0

                        if works_count:
                            course_lessons.append(
                                Lesson(
                                    name=lesson_name,
                                    count=works_count
                                )
                            )

                output.append(
                    Course(
                        name=course_name,
                        id=course_id,
                        lessons=course_lessons
                    )
                )
        for course in output:
            try:
                course.lessons.sort(key=lambda lesson: int(lesson.name.split(".")[0].split()[-1]))
            except ValueError as e:
                print(e)
        return output
