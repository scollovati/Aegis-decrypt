#!/usr/bin/env python3
"""
example usage: aegis-decrypt.py --input ./testdata/aegis_encrypted.json  --entryname Mason
optional --qrcode for output
password: test
"""
import argparse
import getpass
import io
import json
import os
import sys

import pyotp
import pyqrcode

from src.AegisDB import AegisDB
from pprint import pprint


def valid_filename_char(c):
    return c.isalpha() or c.isdigit() or c in "@_-"


def gen_filename(entry):
    parts = []
    label = entry.get('label')
    if label:
        parts.append(label)
    issuer = entry.get('issuer')
    if issuer:
        parts.append(issuer)

    key = '@'.join(parts)

    prefix = "".join([c for c in key if valid_filename_char(c)]).strip()

    candidate = f"{prefix}.svg"
    counter = 0
    while os.path.exists(candidate):
        counter += 1
        candidate = f"{prefix}_{counter}.svg"

    return candidate


def main():
    parser = argparse.ArgumentParser(prog="aegis-decrypt.py",description="FIXME Decrypt an Aegis vault and generate an OTP code", add_help=True)
    parser.add_argument("--vault", dest="vault", required=True, help="encrypted Aegis vault file")
    # optional args
    parser.add_argument("--entryname", dest="entryname", required=False,
                        help="name of the entry for which you want to generate the OTP code")
    parser.add_argument("--output", dest="output", required=False, default="-", choices=['-', 'qrcode', 'json'], help="output file ('-' for stdout)")
    args = parser.parse_args()

    password = getpass.getpass().encode("utf-8")
    db = AegisDB(args.vault)
    entries = db.decrypt_db(password)
    # db.all(entries)

    # exit(2)

    entries_found = db.getByName(entries, args.entryname.lower())

    for entry in entries_found:
        if entry.get('type', '') == 'totp':
            totp = pyotp.TOTP(entry['info']['secret'], interval=entry['info']['period'])

            if args.output == 'qrcode':
                url = totp.provisioning_uri(entry['name'], issuer_name=entry['issuer'])
                if url:
                    img = pyqrcode.create(url)
                    save_filename = gen_filename(entry)
                    img.svg(save_filename, scale=4, background='#fff')
                    print("Code saved as: %s" % save_filename)
            elif args.output == "-":
                print("Entry %s - issuer %s - TOTP generated: %s" % (
                    entry.get('name', ''), entry.get('issuer', ''), totp.now()))
            elif args.output == "json":
                # FIXME insert the full unencrypted json?
                with io.open('export.json', "w") as f:
                    f.write(json.dumps(entries, indent=4))

        else:
            print("OTP type not supported: %s" % entry.get('type', ''))
            sys.exit(2)


if __name__ == '__main__':
    main()
