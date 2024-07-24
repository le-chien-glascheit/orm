# from collections.abc import Callable
# import random
#
#
def product_fabric() -> list[ProductQuantity]:

    products = []
    users = session.execute(select(User.id)).
    for _ in range(random.randint(1, 15)):
        product_quantity = ProductQuantity(
            quantity=random.randint(0, 99999)
        )
        products.append(product_quantity)
    return products


# data_generator(
#     model=Task,
#     fileds={
#         'products': product_fabric
#     },
#     count=70,
#     session=session
# )


def user_gen() -> list:



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


def add_task(session: Session):
    product = Product(name='Морковь', barcode=237200121)
    product_quantity = ProductQuantity(quantity=15)
    product_quantity.product = product
    task = Task()
    task.products.append(product_quantity)

    product_gen: Callable[[], list[ProductQuantity]]
    user_gen: Callable[[], list[User]]

    {'products': product_gen, 'users': user_gen}
    session.add(task)
    # session.add(product)
    session.commit()

