#!/usr/bin/env python3

# example usage: generate_otp.py --input ./testdata/aegis_encrypted.json  --entryname Mason
# optional --qrcode for output
# password: test

import argparse
import getpass
import json
import os
import sys

import pyotp
import pyqrcode

import decrypt
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
    parser = argparse.ArgumentParser(description="Decrypt an Aegis vault and generate an OTP code")
    parser.add_argument("--input", dest="input", required=True, help="encrypted Aegis vault file")
    parser.add_argument("--entryname", dest="entryname", required=True, help="name of the entry for which you want to generate the OTP code")
    parser.add_argument("--qrcode", action="store_true", required=False, help="If the output should be QR code")

    args = parser.parse_args()

    password = getpass.getpass().encode("utf-8")

    db = decrypt.decrypt_db(args.input, password)

    entries = json.loads(db)
    entries_found = []

    for entry in entries['entries']:
        name = entry.get('name', '')

        # Looks also for substrings
        if args.entryname.lower() in name.lower():
            entries_found.append(entry)

    for entry in entries_found:
        if entry.get('type', '') == 'totp':
            if args.qrcode:
                totp = pyotp.TOTP(entry['info']['secret'], interval=entry['info']['period'])
                url = totp.provisioning_uri(entry['name'], issuer_name=entry['issuer'])
                if url:
                    img = pyqrcode.create(url)
                    save_filename = gen_filename(entry)
                    img.svg(save_filename, scale=4, background='#fff')
                    print("Code saved as: %s" % save_filename)
            else:
                totp = pyotp.TOTP(entry['info']['secret'], interval=entry['info']['period'])
                print("Entry %s - issuer %s - TOTP generated: %s" % (
                    entry.get('name', ''), entry.get('issuer', ''), totp.now()))
        else:
            print("OTP type not supported: %s" % entry.get('type', ''))
            sys.exit(2)


if __name__ == '__main__':
    main()