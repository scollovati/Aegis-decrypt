import csv
import io
import json
import os

from src.entry_totp import EntryTOTP

class Output:
    """
    Class to control the output format.
    """

    _FILENAME_PLAIN = "aegis_plain"

    def __init__(self, entries: list, entry_name:str|None = None, export_base_path: str = ".", search_term: str|None = None):
        self._entries = entries
        self._export_path = export_base_path + "/export/"
        self._search_term = search_term

        os.makedirs(os.path.dirname(self._export_path), exist_ok=True)
        if entry_name is None:
            self.file_path = self._export_path + self._FILENAME_PLAIN
        else:
            self.file_path = (
                self._export_path
                + self._FILENAME_PLAIN
                + self._gen_filename(entry_name.lower())
            )


    def stdout(self) -> None:
        # TODO add columns header
        # TODO add groups
        for entry in self._entries:
            
            # Print main entry info
            print(
                f"{entry['uuid']}  {entry['type']:5}  {entry['name']:<45}  {entry['issuer']:<35}  {entry['info']['secret']}  {entry['info']['algo']:6}  {entry['info']['digits']:2}  {entry['info'].get('period', '')}"
            )

            note = entry.get('note', '')
            # Only show note if --search is specified AND note contains the search term
            if self._search_term and note and self._search_term.lower() in note.lower():
                self._print_note_context(note)

    def otpauth(self) -> None:
        # FIXME missing header
        path = self.file_path + "_otpauth.csv"

        # Open file in write mode to overwrite if exists
        with open(path, "w", encoding="utf-8") as f:
            for entry in self._entries:
                if entry.get("type", "") == "totp":
                    totp = EntryTOTP(entry)
                    Lurl = totp.generate_otpauthurl()
                    f.write(Lurl + "\n")
                else:
                    print(
                        f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<30} - OTP type not supported: {entry.get('type', ''):<6}"
                    )

        print(f"Entries unencrypted saved as: {path}")

    def csv(self) -> None:
        # TODO add groups
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
                "note",
            ]
            writer.writerow(header)
            for entry in self._entries:
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
                        entry['note'],
                    ]
                )
            print(f"Entries unencrypted saved as: {path}")

    def otp(self) -> None:
        for entry in self._entries:
            # Print main entry info
            if entry.get("type", "") == "totp":
                totp = EntryTOTP(entry)
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<30} - TOTP generated: {totp.generate_code():<6}"
                )
            else:
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<30} - OTP type not supported: {entry.get('type', ''):<6}"
                )

            note = entry.get('note', '')
            # Only show note if --search is specified AND note contains the search term
            if self._search_term and note and self._search_term.lower() in note.lower():
                self._print_note_context(note)

    def json(self) -> None:
        # TODO add aegis headers and groups
        path = self.file_path + ".json"
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self._entries, indent=4))
            print(
                'WARNING! The produced unencrypted JSON has not the same structure of the Aegis unencrypted export. This JSON contains only the "entries" array.'
            )
            print(f"Unencrypted vault saved as: {path}")

    def qrcode(self) -> None:
        # TODO put all QRcodes in a well formatted PDF
        for entry in self._entries:
            if entry.get("type", "") == "totp":
                totp = EntryTOTP(entry)
                img = totp.generate_qr_code()
                save_filename = (
                    self._export_path
                    + self._gen_filename(entry.get("name"), entry.get("issuer"))
                    + ".png"
                )
                img.png(save_filename, scale=4, background="#fff")
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<35} - TOTP QRCode saved as: {save_filename:<100}"
                )
            else:
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<35} - OTP type not supported: {entry.get('type', ''):<6}"
                )

    def _print_note_context(self, note) -> None:
        note_context = self._get_note_context(note)
        if note_context:
            # Indent note lines for better readability with box drawing characters
            note_lines = note_context.split('\n')
            print("  ┌─ Note:")
            for i, line in enumerate(note_lines):
                if i == len(note_lines) - 1:
                    print(f"  └─ {line}")
                else:
                    print(f"  │  {line}")
            print()  # Empty line after note for separation

    def _get_note_context(self, note: str) -> str:
        """
        Extract context around the search term in the note field.
        Shows up to 20 lines before and after the matching line, stopping at blank lines.
        """
        if not self._search_term or not note:
            return note

        lines = note.split('\n')
        search_lower = self._search_term.lower()

        # Find lines that contain the search term
        matching_indices = [i for i, line in enumerate(lines) if search_lower in line.lower()]

        if not matching_indices:
            return note  # Return full note if no match (shouldn't happen)

        # Collect context lines (up to 20 before and after each match, stopping at blank lines)
        context_lines = set()
        for idx in matching_indices:
            # Add the matching line itself
            context_lines.add(idx)

            # Add lines before (up to 20, stop at blank line)
            for i in range(1, 21):
                prev_idx = idx - i
                if prev_idx < 0:
                    break
                if lines[prev_idx].strip() == "":  # Stop at blank line
                    break
                context_lines.add(prev_idx)

            # Add lines after (up to 20, stop at blank line)
            for i in range(1, 21):
                next_idx = idx + i
                if next_idx >= len(lines):
                    break
                if lines[next_idx].strip() == "":  # Stop at blank line
                    break
                context_lines.add(next_idx)

        # Sort and build the context string
        sorted_indices = sorted(context_lines)
        result_lines = []
        prev_idx = -2

        for idx in sorted_indices:
            if idx > prev_idx + 1:
                result_lines.append("...")
            result_lines.append(lines[idx])
            prev_idx = idx

        if sorted_indices[-1] < len(lines) - 1:
            result_lines.append("...")

        return '\n'.join(result_lines)

    def _valid_filename_char(self, c: str) -> bool:
        return c.isalpha() or c.isdigit() or c in "@_-"

    def _gen_filename(self, entry_name: str, entry_issuer: str | None = None) -> str:
        parts = []
        label = entry_name
        if label:
            parts.append(label)
        issuer = entry_issuer
        if issuer:
            parts.append(issuer)

        key = "@".join(parts)

        prefix = "".join([c for c in key if self._valid_filename_char(c)]).strip()

        candidate = f"{prefix}"

        return candidate
