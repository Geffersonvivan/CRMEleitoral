from io import BytesIO

import qrcode
from django.core.files.base import ContentFile


def generate_qrcode_for_url(url):
    """Gera QR Code PNG como ContentFile do Django."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#002776', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue())
