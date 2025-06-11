from pydantic import BaseModel

class UpdateProfileRequest(BaseModel):
    user_id: str
    name: str
    email: str
    phone_number: str
    contacts_loaded: bool