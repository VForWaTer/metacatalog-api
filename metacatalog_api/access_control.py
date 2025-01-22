import hashlib
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Session, select
from random import choice
from string import ascii_letters, digits

from metacatalog_api.models import PersonTable, Author


class UserTokenBase(SQLModel):
    token_hash: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=datetime.now)
    valid_until: datetime | None = None

class UserTokenTable(UserTokenBase, table=True):
    __tablename__ = 'user_access_tokens'

    id: int = Field(primary_key=True)
    user_id: int | None = Field(default=None,foreign_key='persons.id')
    user: PersonTable | None = Relationship()


class UserToken(UserTokenBase):
    user: Author |  None = None


def register_new_token(session: Session, user: Author | None, valid_until: datetime | None = None) -> str:
    #new_key = Fernet.generate_key().decode()
    new_key = 'k' + ''.join(choice(ascii_letters + digits) for i in range(31))
    token_hash = hashlib.sha256(new_key.encode('utf-8')).hexdigest()

    token = UserTokenTable(
        user_id=user.id if user is not None else None,
        token_hash=token_hash,
        valid_until=valid_until
    )

    session.add(token)
    session.commit()
    return new_key 


def validate_token(session: Session, token: str) -> UserToken | None:
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    user_token = session.exec(select(UserTokenTable).where(UserTokenTable.token_hash ==token_hash)).first()

    return user_token
