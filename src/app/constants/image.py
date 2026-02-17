from enum import StrEnum


class ImageMessage(StrEnum):
    pillow_requeued = 'Pillow backend requested but Pillow is not installed'
    vips_requeued = 'Vips backend requested but vips is not installed'
    unknown_image_backend = 'Unknown backend: {name}'
