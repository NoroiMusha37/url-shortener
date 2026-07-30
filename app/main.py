from fastapi import FastAPI
from app.middlewares import StructlogContextMiddleware

app = FastAPI()

app.add_middleware(StructlogContextMiddleware)
