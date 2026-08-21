from django.conf import settings

FEATURED_CAROUSEL_IMAGES = (
    "IMG_6981.jpeg",
    "IMG_6982.jpeg",
    "_DSC1830.jpeg",
    "_DSC1963.jpeg",
    "_DSC2515.jpeg",
    "_DSC2602.JPEG",
    "_DSC2655.jpeg",
    "gpm2026-1002.jpeg",
    "gpm2026-266.jpeg",
    "gpm2026-330.jpeg",
    "gpm2026-436.jpeg",
    "gpm2026-70.jpeg",
)
FEATURED_CAROUSEL_IMAGE_ORDER = {
    image_name.lower(): index
    for index, image_name in enumerate(FEATURED_CAROUSEL_IMAGES)
}


def current_path(request):
    return {"current_path": request.path}


def _carousel_images():
    carousel_dir = settings.BASE_DIR / "main_site" / "static" / "images" / "carousel"
    image_extensions = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}

    if not carousel_dir.exists():
        return []

    images = [
        image
        for image in carousel_dir.iterdir()
        if image.is_file() and image.suffix.lower() in image_extensions
    ]
    images.sort(key=_carousel_image_sort_key)

    return [f"images/carousel/{image.name}" for image in images]


def _carousel_image_sort_key(image):
    name = image.name.lower()
    return (FEATURED_CAROUSEL_IMAGE_ORDER.get(name, len(FEATURED_CAROUSEL_IMAGES)), name)


def carousel_images(request):
    return {"carousel_images": _carousel_images()}
