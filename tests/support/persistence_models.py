"""Version 1 fixture models, importable without implicitly registering them."""
from enum import Enum, Flag


class Record:
    def __init__(self, value): self.value = value


class RenamedValue:
    def __init__(self, value): self.value = value


class Color(Enum):
    RED = 'red'


class Permission(Flag):
    READ = 1
    WRITE = 2
