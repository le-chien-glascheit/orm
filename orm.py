from datetime import datetime
from random import random
from uuid import uuid4

from sqlalchemy import ForeignKey, create_engine, UUID, Uuid, select, func
from sqlalchemy.orm import (declared_attr, DeclarativeBase, Mapped,
                            mapped_column, relationship, Session, joinedload)


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

    def __repr__(self):
        return f'Product name is {self.name}'


class User(NameMixin, Base):
    password: Mapped[int]

    tasks: Mapped[list['Task']] = relationship(
        secondary='usertask',
        back_populates='users',
    )

    def __repr__(self):
        return f'User({self.name=})'


class Device(NameMixin, Base):
    description: Mapped[str]

    tasks: Mapped[list['Task']] = relationship(
        secondary='devicetask',
        back_populates='devices',
    )

    def __repr__(self):
        return f'Device(name={self.name})'


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

    def __repr__(self):
        return f'Task(id={self.id})'


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
    user3 = User(name='Oleg2', password=646567474)
    device = Device(name='SKF_2000', description='Я прибор, а не документ')
    device2 = Device(name='SKF_2004', description='I AM ROBOT')
    product = Product(name='Морковь', barcode=237200121)
    product2 = Product(name='Эстрагон', barcode=237200543)
    product3 = Product(name='Имбирь', barcode=237200984)
    task = Task()

    task.users.extend([user1, user2])
    task.devices.extend([device])

    for user in user1, user2, user3:
        session.add(user)
    session.add(device)
    session.add(device2)

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



    # random_row = session.query(User).order_by(func.rundom()).first
    # random_row = session.query(User).offset().limit(counter).all



def random_init (session: Session, counter: int):
    for i in range(counter):
        name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(3, 9)))
        password = random.randint(100000000, 999999999)
        user = User(name=name, password=password)
        session.add(user)
    session.commit()



def select_users_by_device_name(session: Session, device_name: str):
    request = session.execute(
        select(Device)
        .where(Device.name == device_name)
        .options(
            joinedload(Device.tasks).options(joinedload(Task.users)),
        )
    )
    users = []
    for device in request.unique().scalars().all():
        for task in device.tasks:
            for user in task.users:
                users.append(user)
    return users


def data_generator(
        model: Base,
        fileds: dict[str, Callable],
        count: int,
        session: Session
) -> None:
    """Генерирует записи соответственно введённой функции."""
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
    # create_tables(engine)
    with Session(engine) as session:
        # task1init(session)
        # do_select(session)
        # print(select_users_by_device_name(session, 'SKF_2000'))
        random_init(session, 2)


if __name__ == '__main__':
    main()
