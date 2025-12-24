from pydantic import BaseModel
from pydantic import BaseModel, Field

class StatusOk(BaseModel):
    status: str = Field(default="Ok", frozen=True)
    
    class Config:
        frozen = True