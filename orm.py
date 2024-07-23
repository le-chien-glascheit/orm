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


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class NameMixin:
    name: Mapped[str]


class Product(NameMixin, Base):
    barcode: Mapped[int]

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


class Task(Base):
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


def create_tables(engine):
    Base.metadata.create_all(engine)


def do_select(session: Session):
    request = session.execute(select(User).options(joinedload(User.tasks)))
    for user in request.unique().scalars().all():
        print(user.name, user.password, [task.id for task in user.tasks])


def select_users_who_use_devices(session: Session, Device=None):
    request = session.execute(select(Device).options(joinedload(Device.tasks)))
    for Device in request.unique().scalars().all():
        print(User.name, [task.id for task in Device.tasks])


def select_task_id_count_product_id(session: Session):
    response = session.execute(
        select(Task.id, func.sum(ProductQuantity.quantity).label("count"))
        .join(ProductQuantity)
        .group_by(Task.id)
    )
    for row in response:
        print(row)


"""
select task.id, sum(productquantity.quantity) as products_count
from task
JOIN productquantity on productquantity.task_id = task.id
GROUP by task.id
"""


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


def main():
    engine = create_engine('sqlite:///db.sqlite3', echo=False)
    create_tables(engine)
    with Session(engine) as session:
        # add_task(session)
        # data_generator(
        #     model=User,
        #     fileds={
        #         'name': lambda*_: ''.join(random.choices(
        #             string.ascii_lowercase,
        #             k=random.randint(7, 24)
        #         )),
        #         'password': lambda*_: random.randint(100000000, 999999999),
        #     },
        #     count=150,
        #     session=session
        # )
        # data_generator(
        #     model=Product,
        #     fileds={
        #         'name': lambda*_: ''.join(random.choices(
        #             string.ascii_lowercase,
        #             k=random.randint(7, 24))),
        #         'barcode': lambda*_: random.randint(100000000, 999999999)
        #     },
        #     count=1300,
        #     session=session
        # )
        # data_generator(
        #     model=Device,
        #     fileds={
        #         'name': lambda*_: 'SKF_' + ''.join(random.choices(
        #             string.hexdigits,
        #             k=random.randint(3, 12))),
        #         'description': lambda*_: ''.join(random.choices(
        #             string.ascii_letters + ' ',
        #             k=random.randint(24, 170)))
        #     },
        #     count=50,
        #     session=session
        # )

        # data_generator(
        #     model=Task,
        #     fileds={
        #         'products': product_fabric,
        #
        #     },
        #     count=70,
        #     session=session,
        # )

        select_task_id_count_product_id(session)
        # add_task(session)

        # do_select(session)
        # select_users_who_use_devices(session)


if __name__ == '__main__':
    main()
