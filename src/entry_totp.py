import pyotp
import pyqrcode
from pyqrcode import QRCode


class EntryTOTP:
    """
    Class to handle the TOTP generation.
    """

    def __init__(self, entry):
        self.entry = entry
        self.totp = pyotp.TOTP(
            entry["info"]["secret"], interval=entry["info"]["period"]
        )

    def generate_code(self) -> str:
        """
        Generate the current TOTP code
        """
        return self.totp.now()

    def generate_qr_code(self) -> QRCode | None:
        """
        Generate the QR Code for the current TOTP entry
        """
        url = self.totp.provisioning_uri(
            self.entry["name"], issuer_name=self.entry["issuer"]
        )
        if url:
            return pyqrcode.create(url)
        return None
