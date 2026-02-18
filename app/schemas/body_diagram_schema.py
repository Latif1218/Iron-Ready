from pydantic import BaseModel

class BodyDiagramResponse(BaseModel):
    front: dict[str, str]  
    back: dict[str, str]
    tips: dict[str, str]  