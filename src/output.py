import csv
import io
import json
import os

from src.entry_totp import EntryTOTP


class Output:
    """
    Class to control the output format.
    """

    export_path = "./export/"

    def __init__(self, entries, entryname=None):
        self.entries = entries
        os.makedirs(os.path.dirname(self.export_path), exist_ok=True)
        if entryname is None:
            self.file_path = self.export_path + "aegis_unencrypted"
        else:
            self.file_path = (
                self.export_path
                + "aegis_unencrypted_"
                + self.gen_filename(entryname.lower())
            )

    def stdout(self):
        # FIXME missing header
        for entry in self.entries:
            print(
                f"{entry['uuid']}  {entry['type']:5}  {entry['name']:<20}  {entry['issuer']:<20}  {entry['info']['secret']}  {entry['info']['algo']:6}  {entry['info']['digits']:2}  {entry['info'].get('period', '')}"
            )

    def csv(self):
        path = self.file_path + ".csv"
        with io.open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header = [
                "uuid",
                "type",
                "name",
                "issuer",
                "secret",
                "algo",
                "digits",
                "period",
            ]
            writer.writerow(header)
            for entry in self.entries:
                writer.writerow(
                    [
                        entry["uuid"],
                        entry["type"],
                        entry["name"],
                        entry["issuer"],
                        entry["info"]["secret"],
                        entry["info"]["algo"],
                        entry["info"]["digits"],
                        entry["info"].get("period", ""),
                    ]
                )

    def otp(self):
        for entry in self.entries:
            if entry.get("type", "") == "totp":
                totp = EntryTOTP(entry)
                print(
                    f"Entry {entry.get("name", "")} - issuer {entry.get("issuer", "")} - TOTP generated: {totp.generate_code()}"
                )
            else:
                print(
                    f"Entry {entry.get("name", "")} - issuer {entry.get("issuer", "")} - OTP type not supported: {entry.get("type", "")}"
                )

    def json(self):
        path = self.export_path + ".json"
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.entries, indent=4))
            print(
                'WARNING! The produced unencrypted JSON has not the same structure of the Aegis unencrypted export. This JSON contains only the "entries" array.'
            )
            print(f"Entries unencrypted saved as: {path}")

    def qrcode(self):
        # FIXME put all QRcodes in PDF
        for entry in self.entries:
            if entry.get("type", "") == "totp":
                totp = EntryTOTP(entry)
                img = totp.generate_qr_code()
                save_filename = (
                    self.export_path
                    + self.gen_filename(entry.get("name"), entry.get("issuer"))
                    + ".svg"
                )
                img.svg(save_filename, scale=4, background="#fff")
                print(
                    f"Entry {entry.get("name", "")} - issuer {entry.get("issuer", "")} - TOTP QRCode saved as: {save_filename}"
                )
            else:
                print(
                    f"Entry {entry.get("name", "")} - issuer {entry.get("issuer", "")} - OTP type not supported: {entry.get("type", "")}"
                )

    def valid_filename_char(self, c):
        return c.isalpha() or c.isdigit() or c in "@_-"

    def gen_filename(self, entry_name, entry_issuer=None):
        parts = []
        label = entry_name
        if label:
            parts.append(label)
        issuer = entry_issuer
        if issuer:
            parts.append(issuer)

        key = "@".join(parts)

        prefix = "".join([c for c in key if self.valid_filename_char(c)]).strip()

        candidate = f"{prefix}"

        return candidate
