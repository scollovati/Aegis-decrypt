import pyotp
import pyqrcode
from pyqrcode import QRCode


class EntryTOTP:
    def __init__(self, entry):
        self.entry = entry
        self.totp = pyotp.TOTP(entry['info']['secret'], interval=entry['info']['period'])

    def generateCode(self) -> str:
        # genero il codice con now, capire se restituire anche la stringa formattata
        return self.totp.now()

    def generateQRCode(self) -> QRCode:
        # genero solo l'oggetto QR code
        url = self.totp.provisioning_uri(self.entry['name'], issuer_name=self.entry['issuer'])
        if url:
            return pyqrcode.create(url)