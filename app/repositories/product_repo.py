# app/repositories/product_repo.py
import uuid

from sqlmodel import Session, select

from app.models.product import Product, ProductImage


class ProductRepository:
    """
    Data access layer for Product & ProductImage.

    - Pure DB operations (CRUD + queries).
    - No FastAPI, no business logic.
    """

    # ----- Products -----

    def get_by_id(self, session: Session, product_id: uuid.UUID) -> Product | None:
        return session.get(Product, product_id)

    def get_by_slug(self, session: Session, slug: str) -> Product | None:
        stmt = select(Product).where(Product.slug == slug)
        return session.exec(stmt).first()

    def list(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 50,
        only_active: bool = True,
    ) -> list[Product]:
        stmt = select(Product)
        if only_active:
            stmt = stmt.where(Product.is_active == True)
        stmt = stmt.offset(skip).limit(limit)
        return session.exec(stmt).all()

    def create(self, session: Session, product: Product) -> Product:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    def update(self, session: Session, product: Product) -> Product:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    def delete(self, session: Session, product: Product) -> None:
        session.delete(product)
        session.commit()

    # ----- Product images -----

    def list_images_for_product(
        self,
        session: Session,
        product_id: uuid.UUID,
    ) -> list[ProductImage]:
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order)
        )
        return session.exec(stmt).all()

    def get_image_by_id(
        self,
        session: Session,
        image_id: uuid.UUID,
    ) -> ProductImage | None:
        return session.get(ProductImage, image_id)

    def create_image(
        self,
        session: Session,
        image: ProductImage,
    ) -> ProductImage:
        session.add(image)
        session.commit()
        session.refresh(image)
        return image

    def delete_image(
        self,
        session: Session,
        image: ProductImage,
    ) -> None:
        session.delete(image)
        session.commit()
