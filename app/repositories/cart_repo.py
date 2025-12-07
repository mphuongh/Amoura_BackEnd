# app/repositories/cart_repo.py
import uuid
from sqlmodel import Session, select
from app.models.cart import CartItem
from app.models.product import Product


class CartRepository:

    # Get items for a user
    def list_for_user(self, session: Session, user_id: uuid.UUID) -> list[CartItem]:
        stmt = select(CartItem).where(CartItem.user_id == user_id)
        return session.exec(stmt).all()

    def get_item(
        self, session: Session, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> CartItem | None:
        stmt = select(CartItem).where(
            CartItem.user_id == user_id, CartItem.product_id == product_id
        )
        return session.exec(stmt).first()

    def get_by_id(self, session: Session, item_id: uuid.UUID) -> CartItem | None:
        return session.get(CartItem, item_id)

    # CRUD
    def create(self, session: Session, item: CartItem) -> CartItem:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

    def update(self, session: Session, item: CartItem) -> CartItem:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

    def delete(self, session: Session, item: CartItem) -> None:
        session.delete(item)
        session.commit()

    def clear_user_cart(self, session: Session, user_id: uuid.UUID) -> None:
        for row in self.list_for_user(session, user_id):
            session.delete(row)
        session.commit()

    def create_from_product(
            self,
            session: Session,
            *,
            user_id: uuid.UUID,
            product: Product,
            quantity: int,
    ) -> CartItem:
        """
        Create a CartItem from a Product, snapshotting:
          - snapshot_price
          - product_name
          - product_hero_image_url

        Business logic (e.g., preventing negative qty) should live in the service.
        """
        item = CartItem(
            user_id=user_id,
            product_id=product.id,
            quantity=quantity,
            snapshot_price=product.price,
            product_name=product.name,
            product_hero_image_url=product.hero_image_url,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
