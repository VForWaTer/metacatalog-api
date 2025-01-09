from pathlib import Path
from starlette.staticfiles import StaticFiles

static_files = StaticFiles(directory=Path(__file__).parent / "templates" / "static")