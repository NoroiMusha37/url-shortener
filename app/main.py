from fastapi import FastAPI

from app.middlewares import StructlogContextMiddleware
from app.routers import auth


app = FastAPI()

app.add_middleware(StructlogContextMiddleware)

app.include_router(auth.router)
