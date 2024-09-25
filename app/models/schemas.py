from pydantic import BaseModel


class ConversionRequest(BaseModel):
    docId: str
    filename: str
    filePath: str
