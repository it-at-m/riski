from pydantic import BaseModel


class Message(BaseModel):
    content: str
    republished: bool = False
