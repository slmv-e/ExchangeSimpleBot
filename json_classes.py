import json
from pydantic import BaseModel, ValidationError


class JsonConfig(BaseModel):
    course_ids: list[int]
    peer_ids: list[int]
    admin_ids: list[int]


class JsonWorker:
    def __init__(self):
        self.path = r"config.json"

    def read(self) -> JsonConfig:
        try:
            return JsonConfig.parse_file(self.path)
        except ValidationError as e:
            print(e)

    def write(self, obj: JsonConfig):
        with open(self.path, "w") as f:
            json.dump(obj.dict(), f, indent=4)
