import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from src.entry_totp import EntryTOTP


class Output:
    """
    Class to control the output format.
    """
    def __init__(
        self,
            entries: list,
            entry_name: str | None = None,
            export_base_path: str = ".",
            search_term: str | None = None,
            source_filename: str | None = None,
    ) -> None:
        self._entries = entries
        self._search_term = search_term
        
        # ----------------------------
        # 1. Determine base directory # base directory = vault location (preferred) or current dir fallback
        # ----------------------------
        if source_filename:
            base_dir = Path(source_filename).resolve().parent
        else:
            base_dir = Path(export_base_path).resolve()
            
        # ----------------------------
        # 2. Create export folder
        # ----------------------------
        self._export_path = base_dir / "export"
        self._export_path.mkdir(parents=True, exist_ok=True)
        
        # ----------------------------
        # 3. Base filename
        # ----------------------------
        base_name = Path(source_filename).stem if source_filename else "aegis-backup"


        # Derive the base name from the source filename (without extension) if provided,
        # otherwise fall back to the default placeholder.
        # ----------------------------
        # 4. Final file path (NO + operators anywhere)
        # ----------------------------
        suffix = "-plain" if entry_name is None else self._gen_filename(entry_name.lower())
        self.file_path = self._export_path / (base_name + suffix)    
        self.file_path = str(self.file_path)   

    def stdout(self) -> None:
        # TODO add columns header
        # TODO add groups
        for entry in self._entries:

            # Print main entry info
            print(
                f"{entry['uuid']}  {entry['type']:5}  {entry['name']:<45}  {entry['issuer']:<35}  {entry['info']['secret']}  {entry['info']['algo']:6}  {entry['info']['digits']:2}  {entry['info'].get('period', '')}"
            )

            note = entry.get("note", "")
            # Only show note if --search is specified AND note contains the search term
            if self._search_term and note and self._search_term.lower() in note.lower():
                self._print_note_context(note)

    def csv_otpauth(self) -> None:
        """
        Keepass compatible output with OtpAuth provisioning urls.
        """
        path = self.file_path + "-otpauth.csv"

        # Open file in write mode to overwrite if exists
        with io.open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header = ["Group", "Title", "Username", "TOTP", "Notes"]
            writer.writerow(header)
            generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for entry in self._entries:
                if entry.get("type", "") == "totp":
                    totp = EntryTOTP(entry)
                    # TODO add group names
                    groups = entry.get("groups", []) or []
                    notes_group = "Group(s) that this item belongs to: " + ",".join(groups) if groups else ""
                    entry_note = entry.get("note", "")
                    if entry_note:
                        separator = " - Notes: " if notes_group else ""
                        notes_group += separator + entry_note
                    writer.writerow(
                        [
                            f"Aegis Export generated on {generated_on}",
                            entry.get("issuer", ""),
                            entry.get("name", ""),
                            totp.generate_otpauthurl(),
                            notes_group,
                        ]
                    )
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
                        entry["note"],
                    ]
                )
            print(f"Entries unencrypted saved as: {path}")

    def otp(self) -> None:
        # Calculate timing info once from TOTP entry with shortest period
        first_totp = None
        min_period = float('inf')
        for entry in self._entries:
            if entry.get("type", "") == "totp":
                period = entry["info"].get("period", 30)
                if period < min_period:
                    min_period = period
                    first_totp = EntryTOTP(entry)
        
        # Display all entries
        for entry in self._entries:
            # Print main entry info
            if entry.get("type", "") == "totp":
                totp = EntryTOTP(entry)
                current_code = totp.generate_code()
                next_code = totp.get_next_code()
                
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<30} - "
                    f"Current TOTP: {current_code:<6} - Next TOTP: {next_code:<6}"
                )
            else:
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<30} - OTP type not supported: {entry.get('type', ''):<6}"
                )

            note = entry.get("note", "")
            # Only show note if --search is specified AND note contains the search term
            if self._search_term and note and self._search_term.lower() in note.lower():
                self._print_note_context(note)
        
        # Display timestamp, progress bar, and timing info once at the end
        if first_totp is not None:
            current_time = first_totp.get_current_timestamp()
            progress_bar = first_totp.get_progress_bar()
            time_remaining = first_totp.get_time_remaining()
            period = first_totp._entry["info"]["period"]
            next_expiry_total = time_remaining + period
            
            print(
                f"\nCurrent TOTP {progress_bar} "
                f"\nNext TOTP expires in {next_expiry_total}s\nCurrent Time: {current_time}"
            )

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
        """
        Generate a single A4 PDF containing all TOTP QR codes,
        each labelled with its entry name (and issuer). Multiple pages
        are created automatically when needed.

        Under each QR code the full otpauth:// URL is printed (wrapped
        to fit the cell width). The source filename and the generation
        date are printed as a header on every page.
        """
        path = self.file_path + "-qrcodes.pdf"

        # --- Page / grid configuration -------------------------------------
        page_width, page_height = A4
        margin = 10 * mm
        cols, rows = 4, 5                       # 20 QR codes per page
        per_page = cols * rows

        usable_width = page_width - 2 * margin
        usable_height = page_height - 2 * margin
        cell_width = usable_width / cols
        cell_height = usable_height / rows

        qr_size = min(cell_width, cell_height) - 12 * mm   # leave room for caption
        qr_frame_padding = 1.5 * mm                        # space between QR and its frame
        caption_font_size = 8
        url_font_size = 5
        url_font_name = "Courier"
        url_line_gap = 1.1                                 # multiplier for line height
        header_font_size = 9
        # -------------------------------------------------------------------

        # Collect only the entries we can actually render
        totp_entries = []
        for entry in self._entries:
            if entry.get("type", "") == "totp":
                totp_entries.append(entry)
            else:
                print(
                    f"Entry {entry.get('name', ''):<45} - Issuer {entry.get('issuer', ''):<35} "
                    f"- OTP type not supported: {entry.get('type', ''):<6}"
                )

        if not totp_entries:
            print("No TOTP entries found - PDF not generated.")
            return

        # Header info: source filename + current date
        source_name = os.path.basename(self.file_path)
        generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_text = f"{source_name} - {len(totp_entries)} Codes - Generated: {generated_on}"

        pdf = canvas.Canvas(path, pagesize=A4)
        pdf.setTitle(header_text)
        pdf.setAuthor("aegis-decrypt")
        pdf.setSubject(header_text)

        def _draw_header() -> None:
            pdf.saveState()
            pdf.setFont("Helvetica-Oblique", header_font_size)
            pdf.setFillColorRGB(0.3, 0.3, 0.3)
            pdf.drawString(margin, page_height - margin / 2, header_text)
            pdf.restoreState()

        def _wrap_to_width(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
            """
            Break a (possibly very long) string into chunks whose rendered
            width does not exceed ``max_width``. Splitting is purely
            character-based, which is exactly what we want for URLs.
            """
            lines: list[str] = []
            current = ""
            for ch in text:
                if pdf.stringWidth(current + ch, font_name, font_size) <= max_width:
                    current += ch
                else:
                    if current:
                        lines.append(current)
                    current = ch
            if current:
                lines.append(current)
            return lines

        _draw_header()

        for index, entry in enumerate(totp_entries):
            position_on_page = index % per_page
            col = position_on_page % cols
            row = position_on_page // cols

            # Cell origin (bottom-left of the cell in PDF coordinates)
            cell_x = margin + col * cell_width
            cell_y = page_height - margin - (row + 1) * cell_height

            # --- Cell separator (light grey, dashed) -----------------------
            pdf.saveState()
            pdf.setStrokeColorRGB(0.75, 0.75, 0.75)
            pdf.setLineWidth(0.3)
            pdf.setDash(2, 2)
            pdf.rect(cell_x, cell_y, cell_width, cell_height, stroke=1, fill=0)
            pdf.restoreState()

            # Generate QR PNG into an in-memory buffer
            totp = EntryTOTP(entry)
            qr_img = totp.generate_qr_code()
            otpauth_url = totp.generate_otpauthurl()
            buffer = io.BytesIO()
            qr_img.png(buffer, scale=4, background="#fff")
            buffer.seek(0)

            # Center the QR image horizontally inside its cell, place near the top
            qr_x = cell_x + (cell_width - qr_size) / 2
            qr_y = cell_y + cell_height - qr_size - 4 * mm

            # --- Frame around the QR code (solid, darker) ------------------
            pdf.saveState()
            pdf.setStrokeColorRGB(0.2, 0.2, 0.2)
            pdf.setLineWidth(0.6)
            pdf.rect(
                qr_x - qr_frame_padding,
                qr_y - qr_frame_padding,
                qr_size + 2 * qr_frame_padding,
                qr_size + 2 * qr_frame_padding,
                stroke=1,
                fill=0,
            )
            pdf.restoreState()

            pdf.drawImage(
                ImageReader(buffer),
                qr_x, qr_y,
                width=qr_size, height=qr_size,
                preserveAspectRatio=True,
                mask="auto",
            )

            # Caption: "<name> (<issuer>)"
            name = entry.get("name", "") or ""
            issuer = entry.get("issuer", "") or ""
            caption = f"{name} ({issuer})" if issuer else name

            pdf.setFont("Courier", caption_font_size)
            text_y = qr_y - qr_frame_padding - 4 * mm
            pdf.drawCentredString(cell_x + cell_width / 2, text_y, caption)

            # --- Full otpauth URL printed under the caption ----------------
            url_max_width = cell_width - 4 * mm
            url_lines = _wrap_to_width(
                otpauth_url, url_font_name, url_font_size, url_max_width
            )
            pdf.setFont(url_font_name, url_font_size)
            pdf.setFillColorRGB(0.25, 0.25, 0.25)
            url_y = text_y - url_font_size - 1 * mm
            for line in url_lines:
                pdf.drawCentredString(cell_x + cell_width / 2, url_y, line)
                url_y -= url_font_size * url_line_gap
            pdf.setFillColorRGB(0, 0, 0)

            # End of page -> flush
            if position_on_page == per_page - 1 and index != len(totp_entries) - 1:
                pdf.showPage()
                _draw_header()

        pdf.save()
        print(f"PDF for {len(totp_entries)} QR Codes saved as: {path}")

    def _print_note_context(self, note) -> None:
        note_context = self._get_note_context(note)
        if note_context:
            # Indent note lines for better readability with box drawing characters
            note_lines = note_context.split("\n")
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

        lines = note.split("\n")
        search_lower = self._search_term.lower()

        # Find lines that contain the search term
        matching_indices = [
            i for i, line in enumerate(lines) if search_lower in line.lower()
        ]

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

        return "\n".join(result_lines)

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
