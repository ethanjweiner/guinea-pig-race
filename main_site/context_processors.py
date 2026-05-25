from django.conf import settings


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
    images.sort(key=lambda image: image.name.lower())

    return [f"images/carousel/{image.name}" for image in images]


def carousel_images(request):
    return {"carousel_images": _carousel_images()}
