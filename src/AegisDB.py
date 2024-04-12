import base64
import io
import json
import sys

import cryptography
import cryptography.exceptions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class AegisDB:
    def __init__(self, db_path):
        self.backend = default_backend()
        self.db_path = db_path

    def __die(self, msg, code=1):
        print(msg, file=sys.stderr)
        exit(code)

    # decrypt the Aegis vault file to a Python object
    def decrypt_db(self, password):
        with io.open(self.db_path, "r") as f:
            data = json.load(f)

        # extract all password slots from the header
        header = data["header"]
        slots = [slot for slot in header["slots"] if slot["type"] == 1]

        # try the given password on every slot until one succeeds
        master_key = None
        for slot in slots:
            # derive a key from the given password
            kdf = Scrypt(
                salt=bytes.fromhex(slot["salt"]),
                length=32,
                n=slot["n"],
                r=slot["r"],
                p=slot["p"],
                backend=self.backend
            )
            key = kdf.derive(password)

            # try to use the derived key to decrypt the master key
            cipher = AESGCM(key)
            params = slot["key_params"]
            try:
                master_key = cipher.decrypt(
                    nonce=bytes.fromhex(params["nonce"]),
                    data=bytes.fromhex(slot["key"]) + bytes.fromhex(params["tag"]),
                    associated_data=None
                )
                break
            except cryptography.exceptions.InvalidTag:
                pass

        if master_key is None:
            self.__die("error: unable to decrypt the master key with the given password")

        # decode the base64 vault contents
        content = base64.b64decode(data["db"])

        # decrypt the vault contents using the master key
        params = header["params"]
        cipher = AESGCM(master_key)
        db = cipher.decrypt(
            nonce=bytes.fromhex(params["nonce"]),
            data=content + bytes.fromhex(params["tag"]),
            associated_data=None
        )

        return json.loads(db.decode("utf-8"))['entries']

    def all(self, entries):
        # FIXME add header and better spacing
        for entry in entries:
            print(f"{entry['uuid']}  {entry['type']:5}  {entry['name']:<20}  {entry['issuer']:<20}  {entry['info']['secret']}  {entry['info']['algo']:6}  {entry['info']['digits']:2}  {entry['info'].get('period', '')}")

    def getByName(self, entries, entryname):
        entries_found = []

        for entry in entries:
            name = entry.get('name', '')

            # Looks also for substrings
            if entryname in name.lower():
                entries_found.append(entry)

        return entries_found