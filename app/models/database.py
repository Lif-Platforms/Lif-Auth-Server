from pydantic import BaseModel
from typing import List

class PermissionsList(BaseModel):
    userId: str
    permissions: List[str]

class RoleList(BaseModel):
    userId: str
    role: str

class UserSearch(BaseModel):
    userId: str
    username: str
    role: str
    permissions: List[str]

class UserInfo(BaseModel):
    userId: str
    username: str
    pronouns: str
    bio: str
    role: str
    permissions: List[str]