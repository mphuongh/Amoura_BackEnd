# app/repositories/order_repo.py
import uuid

from sqlmodel import Session, select

from app.models.order import Order, OrderItem


class OrderRepository:
    """
    Data access layer for orders and order_items.

    NOTE:
      - No commits here; order creation is a multi-step transaction.
        The service is responsible for calling session.commit().
    """

    # ---- Orders ----

    def list_for_user(
        self,
        session: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return session.exec(stmt).all()

    def list_all(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit)
        return session.exec(stmt).all()

    def get_by_id(self, session: Session, order_id: uuid.UUID) -> Order | None:
        return session.get(Order, order_id)

    def create_order(self, session: Session, order: Order) -> Order:
        """
        Insert an Order without committing, but ensure id is populated.
        """
        session.add(order)
        session.flush()  # Assign PK
        session.refresh(order)
        return order

    def update_order(self, session: Session, order: Order) -> Order:
        session.add(order)
        session.flush()
        session.refresh(order)
        return order

    # ---- Order items ----

    def list_items_for_order(
        self,
        session: Session,
        order_id: uuid.UUID,
    ) -> list[OrderItem]:
        stmt = select(OrderItem).where(OrderItem.order_id == order_id)
        return session.exec(stmt).all()

    def create_items(
        self,
        session: Session,
        items: list[OrderItem],
    ) -> list[OrderItem]:
        session.add_all(items)
        session.flush()
        for item in items:
            session.refresh(item)
        return items
