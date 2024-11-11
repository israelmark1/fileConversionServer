from pydantic import BaseModel, Field, field_validator


class ConversionRequest(BaseModel):
    docId: str = Field(..., min_length=1)
    fileName: str = Field(..., min_length=1)
    filePath: str = Field(..., min_length=1)

    @field_validator("docId", "fileName", "filePath")
    def no_default_or_none(cls, value):
        if not value or value.isspace():
            raise ValueError("Field cannot be empty or only whitespace")
        return value

    @field_validator("fileName")
    def valid_file_extension(cls, value):
        valid_extensions = (".pdf", ".docx", ".txt")
        if not any(value.endswith(ext) for ext in valid_extensions):
            raise ValueError(f"fileName must have a valid extension {valid_extensions}")
        return value
