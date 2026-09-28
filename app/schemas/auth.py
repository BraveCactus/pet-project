from pydantic import BaseModel


class TokenPair(BaseModel):
    """Пара токенов для OAuth2."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    """Тело запроса на обновление access-токена."""    

    refresh_token: str