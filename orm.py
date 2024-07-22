from collections.abc import Callable

import string
from datetime import datetime
import random
from uuid import uuid4

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

    tasks: Mapped[list['Task']] = relationship(
        secondary='producttakmtm',
        back_populates='products',
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

    products: Mapped[list[Product]] = relationship(
        secondary='producttakmtm',
        back_populates='tasks'
    )

    devices: Mapped[list['Device']] = relationship(
        secondary='devicetask',
        back_populates='tasks',
    )

    users: Mapped[list['User']] = relationship(
        secondary='usertask',
        back_populates='tasks',
    )


class ProductTakMtm(Base):
    product_id: Mapped[int] = mapped_column(ForeignKey(Product.id))
    task_id: Mapped[int] = mapped_column(ForeignKey(Task.id))
    quantity: Mapped[int | None] = mapped_column(default=None, nullable=True)


class UserTask(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    task_id: Mapped[int] = mapped_column(ForeignKey(Task.id))


class DeviceTask(Base):
    device_id: Mapped[int] = mapped_column(ForeignKey(Device.id))
    task_id: Mapped[int] = mapped_column(ForeignKey(Task.id))


def create_tables(engine):
    Base.metadata.create_all(engine)


def task1init(session: Session):
    user1 = User(name='Max', password=574732477)
    user2 = User(name='Oleg', password=646567475)
    device = Device(name='SKF_2000', description='Я прибор, а не документ')
    product = Product(name='Морковь', barcode=237200121)
    product2 = Product(name='Эстрагон', barcode=237200543)
    product3 = Product(name='Имбирь', barcode=237200984)
    task = Task()

    task.users.extend([user1, user2])

    session.add(user1)
    session.add(user2)
    session.add(device)

    session.add(product)
    session.add(product2)
    session.add(product3)

    session.add(task)
    session.add(task)
    session.add(task)

    session.commit()


def do_select(session: Session):
    request = session.execute(select(User).options(joinedload(User.tasks)))
    for user in request.unique().scalars().all():
        print(user.name, user.password, [task.id for task in user.tasks])

        # def select_users_who_use_devices(session: Session, Device=None):
        #     request = session.execute(select(Device).options(joinedload(Device.tasks)))
        #     for Device in request.unique().scalars().all():
        #         print(User.name, [task.id for task in Device.tasks])

        data_generator(User, {'name': uuid4, 'password': ...}, 16, session)


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
            data[filed] = func()
        session.add(model(**data))
    session.commit()


def random_init_users(session: Session, counter: int):
    for _ in range(counter):
        name = ''.join(random.choices(
            string.ascii_lowercase,
            k=random.randint(3, 9)
        ))
        password = random.randint(100000000, 999999999)
        user = User(name=name, password=password)
        session.add(user)
    session.commit()


def random_init_products(session: Session, counter: int):
    for _ in range(counter):
        name = ''.join(random.choices(
            string.ascii_lowercase,
            k=random.randint(7, 24)
        ))
        barcode = random.randint(100000000, 999999999)
        product = Product(name=name, barcode=barcode)
        session.add(product)
    session.commit()


def random_init_device(session: Session, counter: int):
    for _ in range(counter):
        name = 'SKF_' + ''.join(random.choices(
            # string.ascii_lowercase,
            string.hexdigits,
            k=random.randint(3, 12)
        ))
        description = ''.join(random.choices(
            string.ascii_lowercase,
            k=random.randint(24, 170)
        ))
        device = Device(name=name, description=description)
        session.add(device)
    session.commit()


def main():
    engine = create_engine('sqlite:///db.sqlite3', echo=True)
    create_tables(engine)
    with Session(engine) as session:
        # task1init(session)
        data_generator(
            model=User,
            fileds={
                'name': lambda: ''.join(random.choices(
                    string.ascii_lowercase,
                    k=random.randint(7, 24)
                )),
                'password': lambda: random.randint(100000000, 999999999),
            },
            count=15,
            session=session

        )
        data_generator(
            model=Product,
            fileds={
                'name': lambda: ''.join(random.choices(
                    string.ascii_lowercase,
                    k=random.randint(7, 24))),
                'barcode': lambda: random.randint(100000000, 999999999)
            },
            count=1300,
            session=session
        )

        data_generator(
            model=Device,
            fileds={
                'name': lambda: 'SKF_' + ''.join(random.choices(
                    string.hexdigits,
                    k=random.randint(3, 12))),
                'description': lambda: ''.join(random.choices(
                    string.ascii_letters + ' ',
                    k=random.randint(24, 170)))
            },
            count=50,
            session=session
        )
        # random_init_users(session, 20000)
        # random_init_products(session, 35768)
        # random_init_device(session, 36489)
        # do_select(session)
        # select_users_who_use_devices(session)


if __name__ == '__main__':
    main()
