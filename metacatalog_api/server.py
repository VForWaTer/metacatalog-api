from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from pydantic_settings import BaseSettings, SettingsConfigDict
import uvicorn

from metacatalog_api import core
from metacatalog_api import __version__
from metacatalog_api.db import DB_VERSION


class Server(BaseSettings):
    model_config = SettingsConfigDict(
        cli_parse_args=True, 
        cli_prog_names="metacatalog-server"
    )
    host: str = "0.0.0.0"
    port: int = 8000
    root_path: str = ""
    reload: bool = False
    app_name: str = "explorer"
    autoupgrade: bool = False

    @property
    def uri_prefix(self):
        if self.root_path.startswith('/'):
            path = self.root_path
        else:
            path = f"/{self.root_path}"
        
        if not path.endswith('/'):
            path += '/'
        
        if self.app_name.startswith('/'):
            path += self.app_name.strip('/')
        else:
            path += self.app_name
        
        if not path.endswith('/'):
            return f"{path}/"
        else:
            return path

    def cli_cmd(self, asgi_app: str):
        """Start the uvicorn server"""
        uvicorn.run(asgi_app, host=self.host, port=self.port, root_path=self.root_path, reload=self.reload)

logger = logging.getLogger('uvicorn.error')

# create the server object
server = Server()
logger.info(server.uri_prefix, server.root_path, server.app_name)


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
            if core.db.has_version_mismatch(session):
                if server.autoupgrade:
                    core.migrate_db()
                else:
                    raise ValueError(f"Database version mismatch. Expected version {core.db.DB_VERSION}. Please run database migrations to update your schema.")

    # now we yield the application
    yield

    # here we can app tear down code - i.e. a log message

# build the base app
app = FastAPI(lifespan=lifespan)

@app.get('/version')
def get_version(request: Request):
    return {
        "metacatalog_api": __version__,
        "db_version": DB_VERSION,
        "hostname": request.url.hostname,
        "port": request.url.port,
        "root_path": request.url.path
    }

if __name__ == "__main__":
    print("The main server is not meant to be run directly. Check default_server.py for a sample application")
