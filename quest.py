from collections.abc import Callable

import string
from datetime import datetime
import random
from typing import Optional
from uuid import uuid4

from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr, DeclarativeBase, Mapped, \
    mapped_column, relationship, Session, joinedload
from sqlalchemy import ForeignKey, create_engine, UUID, Uuid, select

DB_URL = 'sqlite:///db.sqlite3'


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class NameMixin:
    name: Mapped[str]


class Product(NameMixin, Base):
    barcode: Mapped[int]
    price: Mapped[int]

    tasks: Mapped[list['ProductQuantity']] = relationship(
        back_populates='product'
    )


class User(NameMixin, Base):
    password: Mapped[int]

    tasks: Mapped[list['Task']] = relationship(
        secondary='usertask',
        back_populates='users',
    )


class Device(NameMixin, Base):
    description: Mapped[str]

    tasks: Mapped[list['Task']] = relationship(
        secondary='devicetask',
        back_populates='devices',
    )


class Task(NameMixin,Base):
    date: Mapped[datetime] = mapped_column(default=datetime.now)
    products: Mapped[list['ProductQuantity']] = relationship(
        back_populates='task'
    )

    devices: Mapped[list['Device']] = relationship(
        secondary='devicetask',
        back_populates='tasks',
    )

    users: Mapped[list['User']] = relationship(
        secondary='usertask',
        back_populates='tasks',
    )


class ProductQuantity(Base):
    product_id: Mapped[int] = mapped_column(ForeignKey(Product.id))
    task_id: Mapped[int] = mapped_column(ForeignKey(Task.id))
    quantity: Mapped[int | None] = mapped_column(default=None, nullable=True)
    task: Mapped['Task'] = relationship(
        back_populates='products'
    )
    product: Mapped['Product'] = relationship(
        back_populates='tasks'
    )


class UserTask(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    task_id: Mapped[int] = mapped_column(ForeignKey(Task.id))


class DeviceTask(Base):
    device_id: Mapped[int] = mapped_column(ForeignKey(Device.id))
    task_id: Mapped[int] = mapped_column(ForeignKey(Task.id))


def do_select(session: Session):
    request = session.execute(select(User).options(joinedload(User.tasks)))
    for user in request.unique().scalars().all():
        print(user.name, user.password, [task.id for task in user.tasks])


def select_users_who_use_devices(session: Session, Device=None):
    request = session.execute(select(Device).options(joinedload(Device.tasks)))
    for Device in request.unique().scalars().all():
        print(User.name, [task.id for task in Device.tasks])


def select_count_product_id_avg_price_sum_price(session: Session):
    """
    SELECT task.id, avg(product.price),
    sum(product.price*productquantity.quantity) as Department_price

    FROM task

    JOIN productquantity ON productquantity.task_id = task.id

    JOIN product ON product.id = productquantity.product_id

    GROUP by task.id
    """
    response = session.execute(
        select(Task.id, func.sum(Product.price * ProductQuantity.quantity))
        .select_from(Task)
        .join(ProductQuantity)
        .join(Product)
        .group_by(Task.id)
    )

    for row in response:
        print(row)


def product_fabric(session: Session) -> list[ProductQuantity]:
    products = []
    product_random = session.execute(
        select(Product.id).offset(random.randint(1, 24)).limit(
            50)).scalars().all()

    for _ in range(random.randint(1, 15)):
        product_quantity = ProductQuantity(
            quantity=random.randint(0, 99999),
            product_id=random.choice(product_random),
        )
        products.append(product_quantity)

    return products


def data_generator(
        model: Base,
        fileds: dict[str, Callable],
        count: int,
        session: Session
) -> None:
    """Генерирует записи соответственно введённой функции.

    :argument model ORM модель Sqlalchemy"""
    for _ in range(count):
        data = dict()
        for filed, func in fileds.items():
            data[filed] = func(session)
        session.add(model(**data))
    session.commit()


def add_task(session: Session):
    product = Product(name='Морковь', barcode=237200121)
    product_quantity = ProductQuantity(quantity=15, product=product)
    task = Task(products=[product_quantity])

    product_gen: Callable[[], list[ProductQuantity]]
    user_gen: Callable[[], list[User]]

    {'products': product_gen, 'users': user_gen}
    session.add(task)
    # session.add(product)
    session.commit()


def init_database(session: Session):
    data_generator(
        model=User,
        fileds={
            'name': lambda *_: ''.join(random.choices(
                string.ascii_lowercase,
                k=random.randint(7, 24)
            )),
            'password': lambda *_: random.randint(100000000, 999999999),
        },
        count=150,
        session=session
    )
    data_generator(
        model=Product,
        fileds={
            'name': lambda *_: ''.join(random.choices(
                string.ascii_lowercase,
                k=random.randint(7, 24))),
            'barcode': lambda *_: random.randint(100000000, 999999999),
            'price': lambda *_: random.randint(20, 99999),
        },
        count=1300,
        session=session
    )
    data_generator(
        model=Device,
        fileds={
            'name': lambda *_: 'SKF_' + ''.join(random.choices(
                string.hexdigits,
                k=random.randint(3, 12))),
            'description': lambda *_: ''.join(random.choices(
                string.ascii_letters + ' ',
                k=random.randint(24, 170)))
        },
        count=50,
        session=session
    )
    data_generator(
        model=Task,
        fileds={
            'products': product_fabric,

        },
        count=70,
        session=session,
    )


def init_for_test(session: Session):
    user1 = User(name='Max', password=574732477)
    user2 = User(name='Oleg', password=646567475)
    user3 = User(name='Kate', password=646567474)
    device1 = Device(name='SKF_2000', description='Я прибор, а не документ')
    device2 = Device(name='SKF_2004', description='I AM ROBOT')
    product1 = Product(name='Морковь', barcode=237200121, price=120)
    product2 = Product(name='Эстрагон', barcode=237200543, price=230)
    product3 = Product(name='Имбирь', barcode=237200984, price=980)
    product4 = Product(name='Томаты', barcode=237201832, price=320)
    product5 = Product(name='Картошка', barcode=237201885, price=80)
    product6 = Product(name='Моцарелла', barcode=237201890, price=570)
    product7 = Product(name='Молоко', barcode=237201820, price=210)
    product8 = Product(name='Творог', barcode=237201853, price=340)
    for user in user1, user2, user3:
        session.add(user)
    for product in (product1, product2, product3, product4, product5,
                    product6, product7, product8):
        session.add(product)


    products_group_a = []
    products_group_b = []

    for product in (product1, product2, product3, product4, product5):
        product_quantity = ProductQuantity(
            quantity=random.randint(0, 5),
            product=product,
        )
        session.add(product_quantity)
        products_group_a.append(product_quantity)


    for product in (product6, product7, product8):
        product_quantity = ProductQuantity(
            quantity=random.randint(0, 5),
            product=product,
        )
        session.add(product_quantity)
        products_group_b.append(product_quantity)

    task1 = Task(products=products_group_a)
    task2 = Task(products=products_group_b)

    task1.devices.extend([device1])
    task2.devices.extend([device2])

    session.add(device1)
    session.add(device2)
    session.add(task1)
    session.add(task2)
    session.commit()


def main():
    engine = create_engine(DB_URL, echo=True)
    with (Session(engine) as session):
        # select_count_product_id_avg_price_sum_price(session)
        # init_for_test(session)
        # select_users_who_use_devices(session)
        select_count_product_id_avg_price_sum_price(session)

if __name__ == '__main__':
    main()
