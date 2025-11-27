# app/services/cart_service.py
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.cart import CartItem
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemRead,
    CartSummary,
)


class CartService:
    """
    Business logic for cart operations.

    Responsibilities:
      - ensure only 'user' accounts use cart (via router dependency)
      - validate product existence and active flag
      - enforce quantity <= stock_on_hand
      - use snapshot_price from Product.price
      - compute line totals and cart totals
    """

    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository):
        self.cart_repo = cart_repo
        self.product_repo = product_repo

    # ---- internal helpers ----

    def _get_valid_product(self, session: Session, product_id: uuid.UUID):
        product = self.product_repo.get_by_id(session, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is inactive",
            )
        return product

    # ---- public operations ----

    def get_cart_summary(
        self,
        session: Session,
        user_id: uuid.UUID,
    ) -> CartSummary:
        """
        Return full cart summary:
          - list of CartItemRead (with line_total)
          - total_quantity
          - total_price
        """
        items = self.cart_repo.list_for_user(session, user_id)

        item_reads: list[CartItemRead] = []
        total_qty = 0
        total_price = 0.0

        for it in items:
            line_total = it.quantity * it.snapshot_price
            total_qty += it.quantity
            total_price += line_total

            item_reads.append(
                CartItemRead(
                    id=it.id,
                    user_id=it.user_id,
                    product_id=it.product_id,
                    quantity=it.quantity,
                    snapshot_price=it.snapshot_price,
                    line_total=line_total,
                    created_at=it.created_at,
                )
            )

        return CartSummary(
            items=item_reads,
            total_quantity=total_qty,
            total_price=total_price,
        )

    def add_to_cart(
        self,
        session: Session,
        user_id: uuid.UUID,
        payload: CartItemCreate,
    ) -> CartSummary:
        """
        Add a product to the user's cart.

        Rules:
          - product must exist and be active
          - quantity + existing_quantity <= stock_on_hand
          - snapshot_price is taken from current product.price
        """
        product = self._get_valid_product(session, payload.product_id)

        if payload.quantity > product.stock_on_hand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock available",
            )

        existing = self.cart_repo.get_item(session, user_id, payload.product_id)

        if existing:
            new_qty = existing.quantity + payload.quantity
            if new_qty > product.stock_on_hand:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not enough stock to increase quantity",
                )
            existing.quantity = new_qty
            self.cart_repo.update(session, existing)
        else:
            item = CartItem(
                user_id=user_id,
                product_id=payload.product_id,
                quantity=payload.quantity,
                snapshot_price=product.price,
            )
            self.cart_repo.create(session, item)

        # Return updated cart summary
        return self.get_cart_summary(session, user_id)

    def update_quantity(
        self,
        session: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        payload: CartItemUpdate,
    ) -> CartSummary:
        """
        Update the quantity of an item in the cart.

        If quantity exceeds stock_on_hand => 400.
        """
        product = self._get_valid_product(session, product_id)
        item = self.cart_repo.get_item(session, user_id, product_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not in cart",
            )

        if payload.quantity > product.stock_on_hand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock available",
            )

        item.quantity = payload.quantity
        self.cart_repo.update(session, item)

        return self.get_cart_summary(session, user_id)

    def remove_item(
        self,
        session: Session,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> CartSummary:
        """
        Remove a product from the cart (if present),
        and return updated summary.
        """
        item = self.cart_repo.get_item(session, user_id, product_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart",
            )

        self.cart_repo.delete(session, item)
        return self.get_cart_summary(session, user_id)

    def clear_cart(
        self,
        session: Session,
        user_id: uuid.UUID,
    ) -> CartSummary:
        """
        Clear all items from the cart and return an empty summary.
        """
        self.cart_repo.clear_user_cart(session, user_id)
        return CartSummary(items=[], total_quantity=0, total_price=0.0)
