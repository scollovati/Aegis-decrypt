#!/usr/bin/env python3
"""
usage: aegis-decrypt.py [-h] --vault VAULT [--entryname ENTRYNAME] [--output {None,csv,qrcode,json,otp}]
password: test
"""
import argparse
import getpass

from src.AegisDB import AegisDB
from src.Output import Output


def main():
    parser = argparse.ArgumentParser(prog="aegis-decrypt.py",
                                     description="FIXME Decrypt an Aegis vault and generate an OTP code", add_help=True)
    parser.add_argument("--vault", dest="vault", required=True, help="encrypted Aegis vault file")
    # optional args
    parser.add_argument("--entryname", dest="entryname", required=False,
                        help="name of the entry for which you want to generate the OTP code")
    parser.add_argument("--output", dest="output", required=False, choices=[None, 'csv', 'qrcode', 'json', 'otp'],
                        help="Output file (default is stdout)")
    args = parser.parse_args()

    password = getpass.getpass().encode("utf-8")
    db = AegisDB(args.vault, password)

    if args.entryname is None:
        entries = db.getAll()
    else:
        entries = db.getByName(args.entryname)

    if entries:
        output = Output(entries)

        match args.output:
            case 'csv':
                print("TODO")
            case 'qrcode':
                output.qrcode()
            case 'json':
                output.json(args.entryname)
            case 'otp':
                output.otp()
            case _:
                output.stdout()
    else:
        print("No entries found")


if __name__ == '__main__':
    main()
