import os

from screepsapi import screepsapi


def get_api() -> screepsapi.API:
    host = os.environ["SCREEPS_HOST"]
    user = os.environ["SCREEPS_USERNAME"]
    password = os.environ["SCREEPS_PASSWORD"]
    return screepsapi.API(user, password, host=host, secure=False)


def get_segment(id: int):
    return get_api().get_segment(id)
