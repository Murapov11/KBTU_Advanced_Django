from typing import Optional, List

from users.schemas import UserShort
from utils.schemas_config import BaseSchema


class BaseProject(BaseSchema):
    name: str
    description: Optional[str]


class CreateProject(BaseProject):
    pass


class CreateProjectResponse(BaseProject):
    id: int


class Project(BaseProject):
    id: int
    users: List[UserShort]


class AddUserToProject(BaseSchema):
    user_id: int
    project_id: int


class ProjectUserLog(BaseSchema):
    id: int
    name: str
