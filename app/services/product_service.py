# app/services/product_service.py
import re
import uuid
from typing import Iterable

from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.storage_utils import (
    upload_to_storage,
    delete_public_url,
    generate_filename,
)
from app.models.product import Product, ProductImage
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


# --- Image config ---

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB per image

ALLOWED_IMAGE_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class ProductService:
    """
    Business logic for Product & ProductImage.

    Responsibilities:
      - slug generation & uniqueness
      - validation beyond pydantic
      - image upload/delete orchestration with Supabase
      - admin-only operations (enforced at router via require_admin)
    """

    def __init__(self, repo: ProductRepository):
        self.repo = repo

    # ----- Helpers -----

    @staticmethod
    def _slugify(raw: str) -> str:
        """
        Basic slugification:
          - lowercase
          - non-alphanumeric -> '-'
          - collapse multiple '-'
          - strip leading/trailing '-'
        """
        value = raw.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = re.sub(r"-+", "-", value)
        value = value.strip("-")
        return value or "product"

    def _ensure_unique_slug(self, session: Session, base_slug: str) -> str:
        """
        Ensure slug is unique by appending -2, -3, ... if needed.
        """
        slug = base_slug
        i = 2
        while self.repo.get_by_slug(session, slug) is not None:
            slug = f"{base_slug}-{i}"
            i += 1
        return slug

    @staticmethod
    def _validate_and_get_ext(content_type: str, file_bytes: bytes) -> str:
        if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported image type. Allowed: JPEG, PNG, WEBP.",
            )

        if len(file_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image too large (max 5MB).",
            )

        return ALLOWED_IMAGE_CONTENT_TYPES[content_type]

    def _upload_hero_image(
        self,
        product_id: uuid.UUID,
        ext: str,
        file_bytes: bytes,
    ) -> str:
        """
        Upload hero image to deterministic path so it can be safely overwritten.

        Path pattern:
            products/<product_id>/hero.<ext>
        """
        path = f"products/{product_id}/hero.{ext}"
        return upload_to_storage(path, file_bytes)

    def _upload_gallery_image(
        self,
        product_id: uuid.UUID,
        ext: str,
        file_bytes: bytes,
    ) -> str:
        """
        Upload a gallery image to a random filename.

        Path pattern:
            products/<product_id>/gallery/<uuid>.<ext>
        """
        filename = generate_filename(ext)
        path = f"products/{product_id}/gallery/{filename}"
        return upload_to_storage(path, file_bytes)

    # ----- Products -----

    def list_products(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 50,
        only_active: bool = True,
    ) -> list[Product]:
        return self.repo.list_products(session, skip=skip, limit=limit, only_active=only_active)

    def get_product(self, session: Session, product_id: uuid.UUID) -> Product:
        product = self.repo.get_by_id(session, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    def create_product(
        self,
        session: Session,
        payload: ProductCreate,
    ) -> Product:
        """
        Create a new product with a unique slug.

        - If slug is provided => slugify & ensure unique.
        - Else => slugify from name & ensure unique.
        """
        raw_slug = payload.slug or payload.name
        base_slug = self._slugify(raw_slug)
        slug = self._ensure_unique_slug(session, base_slug)

        product = Product(
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            price=payload.price,
            stock_on_hand=payload.stock_on_hand,
            is_active=payload.is_active,
            category=payload.category.strip(),
        )
        return self.repo.create(session, product)

    def update_product(
        self,
        session: Session,
        product_id: uuid.UUID,
        payload: ProductUpdate,
    ) -> Product:
        """
        Partial update of a product.

        - If slug is changed, enforce uniqueness.
        """
        product = self.get_product(session, product_id)

        if payload.name is not None:
            product.name = payload.name

        if payload.slug is not None:
            new_base_slug = self._slugify(payload.slug)
            if new_base_slug != product.slug:
                product.slug = self._ensure_unique_slug(session, new_base_slug)

        if payload.description is not None:
            product.description = payload.description

        if payload.price is not None:
            product.price = payload.price

        if payload.stock_on_hand is not None:
            product.stock_on_hand = payload.stock_on_hand

        if payload.is_active is not None:
            product.is_active = payload.is_active

        if payload.hero_image_url is not None:
            product.hero_image_url = payload.hero_image_url

        if payload.category is not None:
            product.category = payload.category

        return self.repo.update(session, product)

    def delete_product(
        self,
        session: Session,
        product_id: uuid.UUID,
    ) -> None:
        """
        Delete a product and all its gallery images, and clean up Storage.
        """
        product = self.get_product(session, product_id)
        images = self.repo.list_images_for_product(session, product_id)

        # Delete hero image if exists
        if product.hero_image_url:
            delete_public_url(product.hero_image_url)

        # Delete gallery images
        for img in images:
            delete_public_url(img.image_url)
            self.repo.delete_image(session, img)

        # Finally delete product row
        self.repo.delete(session, product)

    # ----- Hero image -----

    def set_hero_image(
        self,
        session: Session,
        product_id: uuid.UUID,
        content_type: str,
        file_bytes: bytes,
    ) -> Product:
        """
        Upload or replace the hero image for a product.

        - Validates content type + size.
        - Deletes old hero image from Storage if present.
        - Uploads new hero image to deterministic path.
        """
        product = self.get_product(session, product_id)
        ext = self._validate_and_get_ext(content_type, file_bytes)

        # Best-effort cleanup of previous hero image
        if product.hero_image_url:
            delete_public_url(product.hero_image_url)

        new_url = self._upload_hero_image(product.id, ext, file_bytes)
        product.hero_image_url = new_url

        return self.repo.update(session, product)

    # ----- Gallery images -----

    def list_images(
        self,
        session: Session,
        product_id: uuid.UUID,
    ) -> list[ProductImage]:
        """
        List gallery images for a product (sorted by sort_order).
        """
        self.get_product(session, product_id)
        return self.repo.list_images_for_product(session, product_id)

    def add_gallery_images(
        self,
        session: Session,
        product_id: uuid.UUID,
        files: Iterable[tuple[str, bytes]],
    ) -> list[ProductImage]:
        """
        Upload one or more gallery images for a product.

        Args:
            files: iterable of (content_type, file_bytes)

        Returns:
            List of newly created ProductImage rows.
        """
        product = self.get_product(session, product_id)
        existing_images = self.repo.list_images_for_product(session, product.id)
        next_order = len(existing_images)

        new_images: list[ProductImage] = []

        for idx, (content_type, file_bytes) in enumerate(files):
            ext = self._validate_and_get_ext(content_type, file_bytes)
            url = self._upload_gallery_image(product.id, ext, file_bytes)

            image = ProductImage(
                product_id=product.id,
                image_url=url,
                sort_order=next_order + idx,
            )
            created = self.repo.create_image(session, image)
            new_images.append(created)

        return new_images

    def remove_gallery_image(
        self,
        session: Session,
        product_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        """
        Delete a single gallery image and its Storage file.

        - Ensures the image belongs to the given product_id.
        """
        image = self.repo.get_image_by_id(session, image_id)
        if not image or image.product_id != product_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found for this product",
            )

        # Best-effort Storage cleanup
        delete_public_url(image.image_url)

        self.repo.delete_image(session, image)
