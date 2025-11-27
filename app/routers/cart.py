# app/routers/cart.py
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import require_user
from app.database import get_session
from app.models.user import User
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import CartSummary, CartItemCreate, CartItemUpdate
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])

cart_repo = CartRepository()
product_repo = ProductRepository()
service = CartService(cart_repo, product_repo)


@router.get("", response_model=CartSummary)
def get_my_cart(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Get current user's cart summary.

    Auth:
      - Only role='user' (customer) can access.
      - Admins are forbidden.
    """
    return service.get_cart_summary(session, current_user.id)


@router.post("", response_model=CartSummary)
def add_to_cart(
    payload: CartItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Add product to the current user's cart.

    Returns the updated cart summary.
    """
    return service.add_to_cart(session, current_user.id, payload)


@router.patch("/{product_id}", response_model=CartSummary)
def update_cart_item(
    product_id: uuid.UUID,
    payload: CartItemUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Update quantity of a product in the cart.

    Returns the updated cart summary.
    """
    return service.update_quantity(
        session=session,
        user_id=current_user.id,
        product_id=product_id,
        payload=payload,
    )


@router.delete("/{product_id}", response_model=CartSummary)
def remove_cart_item(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Remove a product from the cart.

    Returns the updated cart summary.
    """
    return service.remove_item(session, current_user.id, product_id)


@router.delete("", response_model=CartSummary)
def clear_cart(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """
    Clear the entire cart.

    Returns an empty cart summary.
    """
    return service.clear_cart(session, current_user.id)
