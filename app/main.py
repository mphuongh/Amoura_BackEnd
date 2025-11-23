from fastapi import FastAPI
from routers import carts, login, inventory, orders, products, users

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to Amoura Backend"}
