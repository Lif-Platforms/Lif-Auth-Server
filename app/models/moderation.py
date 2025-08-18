from pydantic import BaseModel
from typing import List, Optional

class ManagePrivileges(BaseModel):
    userId: str
    role: Optional[str] = None
    permissions: List[str]