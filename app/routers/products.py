# app/routers/products.py
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlmodel import Session

from app.core.auth import require_admin
from app.database import get_session
from app.repositories.product_repo import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProductImageRead,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

repo = ProductRepository()
service = ProductService(repo)


# -------- Public endpoints --------


@router.get("", response_model=list[ProductRead])
def list_products(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 50,
    only_active: bool = True,
):
    """
    List products.

    - Public endpoint.
    - `only_active=True` hides inactive products by default.
    """
    return service.list_products(
        session, skip=skip, limit=limit, only_active=only_active
    )


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    Get a single product by id.

    - Public endpoint.
    """
    return service.get_product(session, product_id)


@router.get(
    "/{product_id}/images",
    response_model=list[ProductImageRead],
)
def list_product_images(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    List gallery images for a product (public).
    """
    return service.list_images(session, product_id)


# -------- Admin endpoints --------


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
):
    """
    Create a new product (admin only).
    """
    return service.create_product(session, payload)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(require_admin)],
)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
):
    """
    Update an existing product (admin only).
    """
    return service.update_product(session, product_id, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_product(
    product_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    Delete a product and its images (admin only).
    """
    service.delete_product(session, product_id)
    return None


@router.post(
    "/{product_id}/hero-image",
    response_model=ProductRead,
    dependencies=[Depends(require_admin)],
    summary="Upload or replace hero image for a product",
)
def upload_hero_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """
    Upload a new hero image for the product.

    - Accepts JPEG, PNG, WEBP.
    - Overwrites any previous hero image.
    """
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing content-type for uploaded file",
        )

    file_bytes = file.file.read()
    return service.set_hero_image(
        session=session,
        product_id=product_id,
        content_type=file.content_type,
        file_bytes=file_bytes,
    )


@router.post(
    "/{product_id}/gallery",
    response_model=list[ProductImageRead],
    dependencies=[Depends(require_admin)],
    summary="Upload one or more gallery images for a product",
)
def upload_gallery_images(
    product_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
):
    """
    Upload one or more gallery images for the product.

    - Accepts JPEG, PNG, WEBP.
    - New images are appended at the end of the gallery (sort_order).
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded",
        )

    payload: list[tuple[str, bytes]] = []
    for f in files:
        if not f.content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing content-type for one of the uploaded files",
            )
        file_bytes = f.file.read()
        payload.append((f.content_type, file_bytes))

    return service.add_gallery_images(
        session=session,
        product_id=product_id,
        files=payload,
    )


@router.delete(
    "/{product_id}/gallery/{image_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
    summary="Delete a gallery image by id",
)
def delete_gallery_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """
    Delete a gallery image for a product (admin only).

    - Also deletes the underlying file from Storage (best-effort).
    """
    service.remove_gallery_image(session, product_id, image_id)
    return {"message": "Gallery image deleted successfully"}
