import os
from PIL import Image, ImageOps
import requests
from tempfile import SpooledTemporaryFile

from ocd_frontend import settings
from ocd_frontend.log import get_source_logger

log = get_source_logger('thumbnails')


class CannotSaveOriginal(Exception):
    """Thrown when a thumbnail cannot be saved"""


class CannotSaveThumbnail(Exception):
    """Thrown when a thumbnail cannot be saved"""


class InvalidThumbnailSize(Exception):
    """Thrown when an invalid thumbnail size is provided"""


def get_thumbnail_path(identifier, thumbnail_size='large'):
    return os.path.join(settings.THUMBNAILS_DIR, identifier[:2],
                        '{}_{}.jpg'.format(identifier[2:], thumbnail_size))


def get_thumbnail_url(identifier, thumbnail_size='large'):
    return os.path.join(settings.THUMBNAIL_URL, identifier[:2],
                        '{}_{}.jpg'.format(identifier[2:], thumbnail_size))


def create_thumbnail(source, identifier, size='large'):
    _size = settings.THUMBNAIL_SIZES.get(size)

    if not _size:
        log.exception('Invalid thumbnail size provided')
        raise InvalidThumbnailSize
    try:
        im = Image.open(source)
        if _size.get('type') == 'crop':
            log.debug('Cropping {}'.format(source))
            imc = ImageOps.fit(im, _size.get('size'), Image.ANTIALIAS)
            imc.save(get_thumbnail_path(identifier, size), 'JPEG', quality=90)
        else:
            log.debug('Resizing {}'.format(source))
            im.thumbnail(_size.get('size'), Image.ANTIALIAS)
            im.save(get_thumbnail_path(identifier, size), 'JPEG', quality=90)
    except IOError:
        log.exception('Could not create thumbnail of {}'.format(source))
        raise CannotSaveThumbnail
