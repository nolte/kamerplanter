from pydantic import BaseModel


class RotationSuccessorSet(BaseModel):
    from_family_key: str
    to_family_key: str
    wait_years: int = 3
