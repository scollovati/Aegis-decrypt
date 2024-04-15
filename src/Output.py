import io
import json
import os

from src.EntryTOTP import EntryTOTP


class Output:
    export_path = './export/'

    def __init__(self, entries):
        self.entries = entries
        os.makedirs(os.path.dirname(self.export_path), exist_ok=True)

    def stdout(self):
        # FIXME missing header
        for entry in self.entries:
            print(
                f"{entry['uuid']}  {entry['type']:5}  {entry['name']:<20}  {entry['issuer']:<20}  {entry['info']['secret']}  {entry['info']['algo']:6}  {entry['info']['digits']:2}  {entry['info'].get('period', '')}")

    def otp(self):
        for entry in self.entries:
            if entry.get('type', '') == 'totp':
                totp = EntryTOTP(entry)
                print("Entry %s - issuer %s - TOTP generated: %s" % (
                entry.get('name', ''), entry.get('issuer', ''), totp.generateCode()))
            else:
                print("Entry %s - issuer %s - OTP type not supported: %s" % (
                entry.get('name', ''), entry.get('issuer', ''), entry.get('type', '')))

    def json(self, entryname = None):
        # FIXME insert the full unencrypted json?
        if entryname is None:
            path = self.export_path + 'aegis_unencrypted.json'
        else:
            path = self.export_path + 'aegis_unencrypted_' + self.gen_filename(entryname.lower()) +'.json'

        with io.open(path, "w") as f:
            f.write(json.dumps(self.entries, indent=4))
            print("Entries unencrypted saved as: %s" % path)

    def qrcode(self):
        # FIXME put all QRcodes in PDF
        for entry in self.entries:
            if entry.get('type', '') == 'totp':
                totp = EntryTOTP(entry)
                img = totp.generateQRCode()
                save_filename = self.export_path + self.gen_filename(entry.get('name'), entry.get('issuer')) + '.svg'
                img.svg(save_filename, scale=4, background='#fff')
                print("Entry %s - issuer %s - TOTP QRCode saved as: %s" % (
                entry.get('name', ''), entry.get('issuer', ''), save_filename))
            else:
                print("Entry %s - issuer %s - OTP type not supported: %s" % (
                entry.get('name', ''), entry.get('issuer', ''), entry.get('type', '')))

    def valid_filename_char(self, c):
        return c.isalpha() or c.isdigit() or c in "@_-"

    def gen_filename(self, entryName, entryIssuer = None):
        parts = []
        label = entryName
        if label:
            parts.append(label)
        issuer = entryIssuer
        if issuer:
            parts.append(issuer)

        key = '@'.join(parts)

        prefix = "".join([c for c in key if self.valid_filename_char(c)]).strip()

        candidate = f"{prefix}"

        return candidate
