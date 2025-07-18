import hashlib
import logging
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Session, select
from random import choice
from string import ascii_letters, digits

from metacatalog_api.models import PersonTable, Author

logger = logging.getLogger('uvicorn.error')


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
    logger.info(f"🔍 Validating token hash: {token_hash[:16]}...")
    
    user_token = session.exec(select(UserTokenTable).where(UserTokenTable.token_hash == token_hash)).first()
    
    if user_token:
        logger.info(f"✅ Token found in database: ID {user_token.id}")
    else:
        logger.info(f"❌ Token not found in database")
    
    return user_token


def is_development_mode(server=None) -> bool:
    """Check if we're running in development mode"""
    if server is None:
        # Import here to avoid circular imports
        from metacatalog_api.server import server as server_instance
        server = server_instance
    # Use the server settings model to check environment
    return server.environment == 'development' or server.admin_token is not None


def create_or_get_admin_user(session: Session, admin_name: str = "admin") -> PersonTable:
    """Create or get an admin user for token generation"""
    # Try to find existing admin user
    admin_user = session.exec(
        select(PersonTable).where(PersonTable.first_name == admin_name)
    ).first()
    
    if admin_user is None:
        # Create new admin user
        admin_user = PersonTable(
            first_name=admin_name,
            last_name="System Administrator",
            is_organisation=False
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        logger.info(f"Created admin user: {admin_user.first_name} {admin_user.last_name} (ID: {admin_user.id})")
    
    return admin_user


def create_admin_token(session: Session, admin_name: str = "admin", valid_until: datetime | None = None) -> str:
    """Create an admin token for development or manual distribution"""
    admin_user = create_or_get_admin_user(session, admin_name)
    token = register_new_token(session, admin_user, valid_until)
    
    logger.info(f"🔑 Admin token created for user '{admin_user.first_name} {admin_user.last_name}' (ID: {admin_user.id})")
    logger.info(f"📋 Token: {token}")
    logger.warning(f"⚠️  Store this token securely - it won't be shown again!")
    
    return token


def get_or_create_admin_token(session: Session, server=None) -> str:
    """Get admin token from environment or create a new one"""
    if server is None:
        # Import here to avoid circular imports
        from metacatalog_api.server import server as server_instance
        server = server_instance
    
    # Check if admin token is provided via server settings
    env_token = getattr(server, 'admin_token', None)
    logger.info(f"🔍 Environment token present: {env_token is not None}")
    
    if env_token:
        logger.info(f"🔑 Checking environment token: {env_token[:10]}...")
        # Validate the environment token to make sure it exists in the database
        validation_result = validate_token(session, env_token)
        if validation_result:
            logger.info(f"✅ Environment token validated successfully")
            return env_token
        else:
            logger.info(f"⚠️  Environment token not found in database, adding it to make it valid...")
            # Add the environment token to the database to make it valid
            admin_user = create_or_get_admin_user(session)
            token_hash = hashlib.sha256(env_token.encode('utf-8')).hexdigest()
            
            token = UserTokenTable(
                user_id=admin_user.id,
                token_hash=token_hash
            )
            session.add(token)
            session.commit()
            logger.info(f"✅ Environment token added to database and is now valid")
            return env_token
    
    # No environment token provided, create a new one
    logger.info(f"🔑 No environment token provided, creating new admin token...")
    return create_admin_token(session)
