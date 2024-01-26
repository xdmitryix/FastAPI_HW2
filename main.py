# Задание
#
# Необходимо создать базу данных для интернет-магазина. База данных должна состоять из трёх таблиц: товары, заказы и пользователи.
# — Таблица «Товары» должна содержать информацию о доступных товарах, их описаниях и ценах.
# — Таблица «Заказы» должна содержать информацию о заказах, сделанных пользователями.
# — Таблица «Пользователи» должна содержать информацию о зарегистрированных пользователях магазина.
# • Таблица пользователей должна содержать следующие поля: id (PRIMARY KEY), имя, фамилия, адрес электронной почты и пароль.
# • Таблица заказов должна содержать следующие поля: id (PRIMARY KEY), id пользователя (FOREIGN KEY), id товара (FOREIGN KEY), дата заказа и статус заказа.
# • Таблица товаров должна содержать следующие поля: id (PRIMARY KEY), название, описание и цена.
#
# Создайте модели pydantic для получения новых данных и возврата существующих в БД для каждой из трёх таблиц (итого шесть моделей).
# Реализуйте CRUD операции для каждой из таблиц через создание маршрутов, REST API (итого 15 маршрутов).
# * Чтение всех
# * Чтение одного
# * Запись
# * Изменение
# * Удаление
#
# Данная промежуточная аттестация оценивается по системе "зачет" / "не зачет"
#
# "Зачет" ставится, если Слушатель успешно выполнил задание.
# "Незачет" ставится, если Слушатель не выполнил задание.
#
# Критерии оценивания:
# 1 - Слушатель создал базу данных для интернет-магазина. База данных должна состоять из трёх таблиц: товары, заказы и пользователи.
# — Таблица «Товары» должна содержать информацию о доступных товарах, их описаниях и ценах.
# — Таблица «Заказы» должна содержать информацию о заказах, сделанных пользователями.
# — Таблица «Пользователи» должна содержать информацию о зарегистрированных пользователях магазина.

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List
import databases
import sqlalchemy
import datetime
import pandas as pd

DATABASE_URL = "sqlite:///my_database.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(40)),
    sqlalchemy.Column("description", sqlalchemy.String),
    sqlalchemy.Column("price", sqlalchemy.Float)
)

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("product_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id")),
    sqlalchemy.Column("date_time", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.String(30))
)

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("first_name", sqlalchemy.String(40)),
    sqlalchemy.Column("second_name", sqlalchemy.String(40)),
    sqlalchemy.Column("email", sqlalchemy.String(100)),
    sqlalchemy.Column("password", sqlalchemy.String(50))
)

engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class User(BaseModel):
    id: int
    first_name: str = Field(max_length=40)
    second_name: str = Field(max_length=40)
    email: str = Field(max_length=100)
    password: str = Field(max_length=50, min_length=5)


class Order(BaseModel):
    id: int
    user_id: int
    product_id: int
    date_time: str
    status: str = Field(max_length=30)


class Product(BaseModel):
    id: int
    name: str = Field(max_length=40)
    description: str
    price: float


@app.get("/")
async def index():
    return {"message": "working..."}


@app.post("/create_user/", response_model=User)
async def create_user(user: User):
    query = users.insert().values(first_name=user.first_name,
                                  second_name=user.second_name,
                                  email=user.email,
                                  password=user.password)
    last_record_id = await database.execute(query)
    return {**user.model_dump(), "id": last_record_id}


@app.get("/users/", response_model=List[User])
async def read_users(request: Request):
    query = users.select()
    user_table = pd.DataFrame([user for user in await database.fetch_all(query)]).to_html()
    return templates.TemplateResponse("users.html", {"request": request, "user_table": user_table})


@app.get("/users/{user_id}", response_model=User)
async def read_user(request: Request, user_id: int):
    query = users.select().where(users.c.id == user_id)
    user_table = pd.DataFrame([user for user in await database.fetch_all(query)]).to_html()
    return templates.TemplateResponse("users.html", {"request": request, "user_table": user_table})


@app.put("/upd_user/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: User):
    query = users.update().where(users.c.id == user_id).values(first_name=new_user.first_name,
                                                               second_name=new_user.second_name,
                                                               email=new_user.email,
                                                               password=new_user.password)
    await database.execute(query)
    return {**new_user.model_dump(), "id": user_id}


@app.delete("/del_user/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {"message": "user_delete"}


@app.post("/create_order/", response_model=Order)
async def create_order(order: Order):
    query = orders.insert().values(user_id=order.user_id,
                                   product_id=order.product_id,
                                   date_time=datetime.date.today(),
                                   status=order.status
                                   )
    last_record_id = await database.execute(query)
    return {**order.model_dump(), "id": last_record_id}


@app.get("/orders/", response_model=List[Order])
async def read_orders(request: Request):
    query = orders.select()
    order_table = pd.DataFrame([order for order in await database.fetch_all(query)]).to_html()
    return templates.TemplateResponse("orders.html", {"request": request, "order_table": order_table})


@app.get("/orders/{order_id}", response_model=Order)
async def read_order(request: Request, order_id: int):
    query = orders.select().where(orders.c.id == order_id)
    order_table = pd.DataFrame([order for order in await database.fetch_all(query)]).to_html()
    return templates.TemplateResponse("orders.html", {"request": request, "order_table": order_table})


@app.put("/upd_order/{order_id}", response_model=Order)
async def update_order(order_id: int, new_order: Order):
    query = orders.update().where(orders.c.id == order_id).values(user_id=new_order.user_id,
                                                                  product_id=new_order.product_id,
                                                                  date_time=datetime.date.today(),
                                                                  status=new_order.status)
    await database.execute(query)
    return {**new_order.model_dump(), "id": order_id}


@app.delete("/del_order/{order_id}")
async def delete_order(order_id: int):
    query = orders.delete().where(orders.c.id == order_id)
    await database.execute(query)
    return {"message": "order_delete"}


@app.post("/create_product/", response_model=Product)
async def create_product(product: Product):
    query = products.insert().values(name=product.name,
                                     description=product.description,
                                     price=product.price
                                     )
    last_record_id = await database.execute(query)
    return {**product.model_dump(), "id": last_record_id}


@app.get("/products/", response_model=List[Product])
async def read_products(request: Request):
    query = products.select()
    product_table = pd.DataFrame([product for product in await database.fetch_all(query)]).to_html()
    return templates.TemplateResponse("products.html", {"request": request, "product_table": product_table})


@app.get("/products/{product_id}", response_model=Product)
async def read_product(request: Request, product_id: int):
    query = products.select().where(products.c.id == product_id)
    product_table = pd.DataFrame([product for product in await database.fetch_all(query)]).to_html()
    return templates.TemplateResponse("products.html", {"request": request, "product_table": product_table})


@app.put("/upd_product/{product_id}", response_model=Product)
async def update_product(product_id: int, new_product: Product):
    query = products.update().where(products.c.id == product_id).values(name=new_product.name,
                                                                        description=new_product.description,
                                                                        price=new_product.price)
    await database.execute(query)
    return {**new_product.model_dump(), "id": product_id}


@app.delete("/del_product/{product_id}")
async def delete_product(product_id: int):
    query = products.delete().where(products.c.id == product_id)
    await database.execute(query)
    return {"message": "product_delete"}
