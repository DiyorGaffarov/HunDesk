import ast
import os
import struct
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def _unquote(text: str) -> str:
    return ast.literal_eval(text)


def parse_po(po_path: Path) -> dict[str, str]:
    messages: dict[str, str] = {}
    msgid = None
    msgstr = None
    section = None
    fuzzy = False

    def finalize_entry():
        nonlocal msgid, msgstr, fuzzy
        if msgid is not None and msgstr is not None and not fuzzy:
            messages[msgid] = msgstr
        msgid = None
        msgstr = None
        fuzzy = False

    for raw_line in po_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line.startswith("#,") and "fuzzy" in line:
            fuzzy = True
            continue

        if not line:
            finalize_entry()
            section = None
            continue

        if line.startswith("#"):
            continue

        if line.startswith("msgid "):
            finalize_entry()
            msgid = _unquote(line[6:])
            msgstr = ""
            section = "msgid"
            continue

        if line.startswith("msgstr "):
            msgstr = _unquote(line[7:])
            section = "msgstr"
            continue

        if line.startswith('"'):
            part = _unquote(line)
            if section == "msgid":
                msgid = (msgid or "") + part
            elif section == "msgstr":
                msgstr = (msgstr or "") + part
            continue

    finalize_entry()
    return messages


def write_mo(messages: dict[str, str], mo_path: Path) -> None:
    keys = sorted(messages.keys())
    ids = b""
    strs = b""
    offsets: list[tuple[int, int, int, int]] = []

    for key in keys:
        msgid_bytes = key.encode("utf-8")
        msgstr_bytes = messages[key].encode("utf-8")
        offsets.append((len(msgid_bytes), len(ids), len(msgstr_bytes), len(strs)))
        ids += msgid_bytes + b"\0"
        strs += msgstr_bytes + b"\0"

    keystart = 7 * 4
    valuestart = keystart + len(keys) * 8
    id_offset = valuestart + len(keys) * 8
    str_offset = id_offset + len(ids)

    output = struct.pack("Iiiiiii", 0x950412DE, 0, len(keys), keystart, valuestart, 0, 0)
    output += b"".join(struct.pack("II", length, offset + id_offset) for length, offset, _, _ in offsets)
    output += b"".join(struct.pack("II", length, offset + str_offset) for _, _, length, offset in offsets)
    output += ids
    output += strs

    mo_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mo_path, "wb") as fh:
        fh.write(output)


class Command(BaseCommand):
    help = "Compile locale .po files to .mo without external gettext/msgfmt dependency."

    def handle(self, *args, **options):
        compiled_count = 0
        for locale_dir in settings.LOCALE_PATHS:
            locale_root = Path(locale_dir)
            if not locale_root.exists():
                continue
            for po_file in locale_root.glob("*/LC_MESSAGES/*.po"):
                mo_file = po_file.with_suffix(".mo")
                messages = parse_po(po_file)
                write_mo(messages, mo_file)
                rel_po = os.path.relpath(po_file, settings.BASE_DIR)
                rel_mo = os.path.relpath(mo_file, settings.BASE_DIR)
                self.stdout.write(self.style.SUCCESS(f"Compiled {rel_po} -> {rel_mo}"))
                compiled_count += 1

        if not compiled_count:
            self.stdout.write(self.style.WARNING("No .po files found in LOCALE_PATHS."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Done. Compiled {compiled_count} locale file(s)."))
