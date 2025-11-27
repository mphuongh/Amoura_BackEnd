# app/routers/orders.py
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import require_user, require_admin
from app.database import get_session
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.order import (
    OrderCreate,
    OrderRead,
    OrderWithItemsRead,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])

order_repo = OrderRepository()
cart_repo = CartRepository()
product_repo = ProductRepository()
service = OrderService(order_repo, cart_repo, product_repo)


# -------- User-facing endpoints --------


@router.post(
    "/checkout",
    response_model=OrderWithItemsRead,
)
def checkout(
    payload: OrderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Create an order from the current user's cart.

    Auth:
      - Only role='user' (customer) can checkout.
    """
    return service.create_order_from_cart(session, current_user.id, payload)


@router.get(
    "/me",
    response_model=list[OrderRead],
)
def list_my_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
    skip: int = 0,
    limit: int = 50,
):
    """
    List the authenticated user's orders (without items).
    """
    return service.list_user_orders(session, current_user.id, skip, limit)


@router.get(
    "/me/{order_id}",
    response_model=OrderWithItemsRead,
)
def get_my_order(
    order_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Get a single order (with items) belonging to the current user.
    """
    return service.get_user_order(session, current_user.id, order_id)


# -------- Admin endpoints --------


@router.get(
    "",
    response_model=list[OrderRead],
    dependencies=[Depends(require_admin)],
)
def list_all_orders(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 50,
):
    """
    List all orders (admin only).
    """
    return service.list_all_orders(session, skip, limit)


@router.get(
    "/{order_id}",
    response_model=OrderWithItemsRead,
    dependencies=[Depends(require_admin)],
)
def get_order_admin(
    order_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    Get any order with items (admin only).
    """
    return service.get_order_admin(session, order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_admin)],
)
def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    session: Session = Depends(get_session),
):
    """
    Update order status (admin only) with simple state machine.

      pending   -> confirmed, canceled

      confirmed -> shipped, canceled

      shipped   -> (no change)

      canceled  -> (no change)

    """
    return service.update_status(session, order_id, payload)
