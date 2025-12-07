# app/services/order_service.py
import uuid
from datetime import datetime, time, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.order import Order, OrderItem
from app.models.cart import CartItem
from app.models.product import Product
from app.repositories.order_repo import OrderRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.order import (
    OrderCreate,
    OrderRead,
    OrderWithItemsRead,
    OrderItemRead,
    OrderStatusUpdate,
)

# Minimum lead time for any delivery
MIN_LEAD_MINUTES = 30

# Canonical start times for each delivery window
WINDOW_START_TIMES: dict[str, time] = {
    "morning": time(9, 0),
    "afternoon": time(14, 0),
    "evening": time(19, 0),
    # "custom" handled specially
}

# Fixed tax rate (8%)
TAX_RATE = 0.08


class OrderService:
    """
    Business logic for orders.

    Responsibilities:
      - Create order from cart
      - Validate cart items against products (stock, active)
      - Compute totals and line_totals
      - Deduct stock_on_hand
      - Clear cart after success
      - Enforce simple status transitions (admin)
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        cart_repo: CartRepository,
        product_repo: ProductRepository,
    ):
        self.order_repo = order_repo
        self.cart_repo = cart_repo
        self.product_repo = product_repo

    # -------- User-facing operations --------

    def create_order_from_cart(
        self,
        session: Session,
        user_id: uuid.UUID,
        payload: OrderCreate,
    ) -> OrderWithItemsRead:
        """
        Convert the current user's cart into an Order.

        Steps:
          1. Validate delivery date (not in the past).
          2. Load cart items; error if empty.
          3. For each cart item:
             - Ensure product exists & is active.
             - Ensure quantity <= stock_on_hand.
             - Ensure snapshot_price > 0.
          4. Compute total_amount from cart.
          5. Create Order row (status='pending').
          6. Create OrderItem rows based on cart.
          7. Deduct product stock_on_hand.
          8. Clear cart.
          9. Commit transaction and return full order.
        """
        # 1) Delivery date/time sanity check
        self._validate_delivery_timing(payload)

        # 2) Load cart
        cart_items: list[CartItem] = self.cart_repo.list_for_user(session, user_id)
        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty",
            )

        # 3) Validate each cart item vs product
        errors: list[dict[str, str]] = []
        product_map: dict[uuid.UUID, Product] = {}

        for ci in cart_items:
            product = self.product_repo.get_by_id(session, ci.product_id)
            product_map[ci.product_id] = product

            if not product:
                errors.append(
                    {
                        "product_id": str(ci.product_id),
                        "reason": "Product not found",
                    }
                )
                continue

            if not product.is_active:
                errors.append(
                    {
                        "product_id": str(ci.product_id),
                        "reason": "Product is inactive",
                    }
                )
                continue

            if ci.quantity > product.stock_on_hand:
                errors.append(
                    {
                        "product_id": str(ci.product_id),
                        "reason": f"Insufficient stock (have {product.stock_on_hand}, requested {ci.quantity})",
                    }
                )
                continue

            if ci.snapshot_price <= 0:
                errors.append(
                    {
                        "product_id": str(ci.product_id),
                        "reason": "Invalid price in cart",
                    }
                )

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Cart validation failed", "items": errors},
            )

        # 4) Compute subtotal and total with tax
        subtotal = 0.0
        for ci in cart_items:
            subtotal += ci.quantity * ci.snapshot_price

        if subtotal <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total order amount must be positive",
            )

        tax_amount = round(subtotal * TAX_RATE, 2)
        total_amount = subtotal + tax_amount

        # 5) Create the Order
        order = Order(
            user_id=user_id,
            receiver_name=payload.receiver_name,
            phone_number=payload.phone_number,
            note=payload.note,
            full_address=payload.full_address,
            province=payload.province,
            ward=payload.ward,
            delivery_date=payload.delivery_date,
            delivery_window=payload.delivery_window,
            status="pending",
            total_amount=total_amount,
        )
        order = self.order_repo.create_order(session, order)

        # 6) Create OrderItem rows (pre-tax unit_price)
        order_items: list[OrderItem] = []
        for ci in cart_items:
            product = product_map.get(ci.product_id)
            product_name: str | None = getattr(ci, "product_name", None)
            if not product_name and product is not None:
                product_name = product.name
            product_hero_image_url: str | None = getattr(
                ci, "product_hero_image_url", None
            )
            if not product_hero_image_url and product is not None:
                product_hero_image_url = product.hero_image_url
            order_items.append(
                OrderItem(
                    order_id=order.id,
                    product_id=ci.product_id,
                    quantity=ci.quantity,
                    unit_price=ci.snapshot_price,
                    product_name=product_name,
                    product_hero_image_url=product_hero_image_url,
                )
            )

        order_items = self.order_repo.create_items(session, order_items)

        # 7) Deduct stock_on_hand
        for ci in cart_items:
            product = product_map[ci.product_id]
            product.stock_on_hand -= ci.quantity
            if product.stock_on_hand < 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal stock calculation error",
                )

        # 8) Clear cart
        for ci in cart_items:
            session.delete(ci)

        # 9) Commit transaction
        session.commit()
        session.refresh(order)

        return self._build_order_with_items_dto(order, order_items)

    def list_user_orders(
        self,
        session: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[OrderRead]:
        """
        List orders for the given user (without items).
        """
        orders = self.order_repo.list_for_user(session, user_id, skip, limit)
        # Pydantic/SQLModel will map to OrderRead automatically via response_model.
        return orders  # type: ignore[return-value]

    def get_user_order(
        self,
        session: Session,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> OrderWithItemsRead:
        """
        Get a single order for the user, including items.

        - 404 if order not found or does not belong to this user.
        """
        order = self.order_repo.get_by_id(session, order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        items = self.order_repo.list_items_for_order(session, order.id)
        return self._build_order_with_items_dto(order, items)

    # -------- Admin operations --------

    def list_all_orders(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 50,
    ) -> list[OrderRead]:
        """
        List all orders (admin only).
        """
        orders = self.order_repo.list_all(session, skip, limit)
        return orders  # type: ignore[return-value]

    def get_order_admin(
        self,
        session: Session,
        order_id: uuid.UUID,
    ) -> OrderWithItemsRead:
        """
        Get any order with items (admin only).
        """
        order = self.order_repo.get_by_id(session, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        items = self.order_repo.list_items_for_order(session, order.id)
        return self._build_order_with_items_dto(order, items)

    def update_status(
        self,
        session: Session,
        order_id: uuid.UUID,
        payload: OrderStatusUpdate,
    ) -> OrderRead:
        """
        Admin-only status update with simple state machine:

          pending   -> confirmed, canceled
          confirmed -> shipped, canceled
          shipped   -> (no change)
          canceled  -> (no change)

        Any invalid transition raises 400.
        """
        order = self.order_repo.get_by_id(session, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        current = order.status
        new = payload.status

        if current == new:
            return order

        allowed = {
            "pending": {"confirmed", "canceled"},
            "confirmed": {"shipped", "canceled"},
            "shipped": set(),
            "canceled": set(),
        }

        if current not in allowed or new not in allowed[current]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: {current} -> {new}",
            )

        order.status = new
        self.order_repo.update_order(session, order)
        session.commit()
        session.refresh(order)
        return order  # type: ignore[return-value]

    # -------- Helper DTO builder --------

    def _build_order_with_items_dto(
        self,
        order: Order,
        items: list[OrderItem],
    ) -> OrderWithItemsRead:
        """
        Compose OrderWithItemsRead from ORM models, including subtotal + tax.
        """
        item_dtos: list[OrderItemRead] = []
        subtotal = 0.0

        for it in items:
            line_total = it.quantity * it.unit_price
            subtotal += line_total
            item_dtos.append(
                OrderItemRead(
                    id=it.id,
                    order_id=it.order_id,
                    product_id=it.product_id,
                    quantity=it.quantity,
                    unit_price=it.unit_price,
                    line_total=line_total,
                )
            )

        tax_amount = round(subtotal * TAX_RATE, 2)

        return OrderWithItemsRead(
            id=order.id,
            user_id=order.user_id,
            receiver_name=order.receiver_name,
            phone_number=order.phone_number,
            note=order.note,
            full_address=order.full_address,
            province=order.province,
            ward=order.ward,
            delivery_date=order.delivery_date,
            delivery_window=order.delivery_window,  # Literal
            status=order.status,  # Literal
            total_amount=order.total_amount,
            created_at=order.created_at,
            items=item_dtos,
            subtotal=subtotal,
            tax_amount=tax_amount,
        )

    def _validate_delivery_timing(self, payload: OrderCreate) -> None:
        """
        Ensure delivery is not in the past and respects MIN_LEAD_MINUTES.
        """
        now = datetime.now()
        today = now.date()

        if payload.delivery_date < today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery date cannot be in the past",
            )

        if payload.delivery_date > today:
            return

        window = payload.delivery_window
        start_time = WINDOW_START_TIMES.get(window)

        if start_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom same-day delivery is not allowed. "
                "Choose a later date or a predefined window.",
            )

        delivery_dt = datetime.combine(payload.delivery_date, start_time)
        min_allowed = now + timedelta(minutes=MIN_LEAD_MINUTES)

        if delivery_dt < min_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Delivery must be at least {MIN_LEAD_MINUTES} minutes "
                    "from now for the selected time window."
                ),
            )
