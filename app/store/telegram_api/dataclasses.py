from dataclasses import dataclass


@dataclass
class Message:
    chat_id: int
    text: str
    inline_data: list | None = None


@dataclass
class UpdateMessage:
    id: int
    chat_id: int
    from_id: int
    username: str
    text: str


@dataclass
class CallbackQuery:
    id: int
    chat_id: int
    from_id: int
    username: str
    text: str
    data: str

@dataclass
class UpdateObject:
    id: int
    type: str
    object: UpdateMessage | CallbackQuery
