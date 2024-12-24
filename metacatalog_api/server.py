from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import uvicorn

from metacatalog_api import core


logger = logging.getLogger('uvicorn.error')

# before we initialize the app, we check that the database is installed and up to date
@asynccontextmanager
async def lifespan(app: FastAPI):
    # check if the entries table can be found in the database
    with core.connect() as session:
        if not core.db.check_installed(session):
            logger.info("Database not installed, installing...")
            core.db.install(session, populate_defaults=True)
            logger.info("Database installed.")
    
    # after checking the database, we check the version
    with core.connect() as session:
        core.db.check_db_version(session)

    # now we yield the application
    yield

    # here we can app tear down code - i.e. a log message

# build the base app
app = FastAPI(lifespan=lifespan)


class Server(BaseSettings):
    model_config = SettingsConfigDict(
        cli_parse_args=True, 
        cli_prog_names="metacatalog-server"
    )
    asgi_app: str = Field(..., exclude=True, env=None)
    host: str = "0.0.0.0"
    port: int = 8000
    root_path: str = "/"
    reload: bool = False

    def cli_cmd(self):
        """Start the uvicorn server"""
        uvicorn.run(self.asgi_app, host=self.host, port=self.port, root_path=self.root_path, reload=self.reload)



if __name__ == "__main__":
    print("The main server is not meant to be run directly. Check default_server.py for a sample application")
