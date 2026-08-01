from fastapi import FastAPI

from app.middlewares import StructlogContextMiddleware
from app.routers import auth, links


app = FastAPI()

app.add_middleware(StructlogContextMiddleware)

app.include_router(auth.router)
app.include_router(links.router)
