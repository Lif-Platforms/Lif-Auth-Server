from pydantic import BaseModel
from typing import Literal

class TwoFaStatus(BaseModel):
    status: Literal["DISABLED", "WAITING_APPROVAL", "ENABLED"]