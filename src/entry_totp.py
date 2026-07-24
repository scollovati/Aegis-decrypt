import time
from datetime import datetime
import pyotp
import pyqrcode
from pyqrcode import QRCode

import hashlib

class EntryTOTP:
    """
    Class to handle the TOTP generation.
    """

    _HASHLIB_ALGO_MAP = {
        "SHA1":   hashlib.sha1,
        "SHA256": hashlib.sha256,
        "SHA512": hashlib.sha512,
        "MD5":    hashlib.md5,
    }

    def __init__(self, entry):
        self._entry = entry
        self._totp = pyotp.TOTP(
            s=entry["info"]["secret"],
            digits=entry["info"]["digits"],
            digest=self._resolve_hash_algo(entry["info"]["algo"]),
            name=entry["name"],
            issuer=entry["issuer"],
            interval=entry["info"]["period"]
        )

    def generate_code(self) -> str:
        """
        Generate the current TOTP code
        """
        return self._totp.now()

    def generate_otpauthurl(self) -> str:
        """
        Generate the otpauth url for the current TOTP entry
        """
        url = self._totp.provisioning_uri(
            self._entry["name"], issuer_name=self._entry["issuer"]
        )
        if url:
            return url
        raise Exception(
            f"Unable to generate otpauth url for entry {self._entry['name']} with issuer {self._entry['issuer']}"
        )

    def generate_qr_code(self) -> QRCode:
        """
        Generate the QR Code for the current TOTP entry
        """
        url = self._totp.provisioning_uri(
            self._entry["name"], issuer_name=self._entry["issuer"]
        )
        if url:
            return pyqrcode.create(content=url, error='H')
        raise Exception(
            f"Unable to generate QR Code for entry {self._entry['name']} with issuer {self._entry['issuer']}"
        )

    def get_time_remaining(self) -> int:
        """
        Get the number of seconds remaining until the current TOTP expires
        """
        current_time = int(time.time())
        period = self._entry["info"]["period"]
        return period - (current_time % period)

    def get_next_code(self) -> str:
        """
        Generate the next TOTP code (after current one expires)
        """
        current_time = int(time.time())
        period = self._entry["info"]["period"]
        # Calculate time for next period
        next_period_time = current_time + (period - (current_time % period))
        return self._totp.at(next_period_time)

    def get_current_timestamp(self) -> str:
        """
        Get current timestamp in readable format
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_progress_bar(self) -> str:
        """
        Get a visual progress bar showing time elapsed with numeric labels
        Bar is scaled to fixed width (30 chars) for readability
        """
        time_remaining = self.get_time_remaining()
        period = self._entry["info"]["period"]
        elapsed = period - time_remaining
        
        # Scale to fixed width (30 chars) for better readability
        bar_width = 30
        filled_width = int((elapsed / period) * bar_width)
        empty_width = bar_width - filled_width
        bar = "█" * filled_width + "░" * empty_width
        
        return f"[{bar}] {elapsed}s/{period}s ({time_remaining}s left)"
    
    def _resolve_hash_algo(self, algo: str):
        """
        Map an Aegis ``entry["info"]["algo"]`` value to the matching
        hashlib constructor (e.g. ``hashlib.sha1``).
        Raises ValueError for unsupported algorithms.
        """
        try:
            return self._HASHLIB_ALGO_MAP[algo.upper()]
        except KeyError as exc:
            raise ValueError(f"Unsupported hash algorithm: {algo!r}") from exc
