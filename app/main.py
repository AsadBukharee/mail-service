from fastapi import FastAPI
from app.database import Base, engine
from app.routers import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mailer Service")

app.include_router(router)
