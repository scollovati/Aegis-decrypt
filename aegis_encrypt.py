#!/usr/bin/env python3
import io
import json

from src.aegis_db import AegisDB
import sys


def main() -> None:
    plain = "./testdata/aegis-backup-plain.json"
    encrypted = "./testdata/aegis-backup-encrypted-TEST.json"

    print(f"Use this script at your own risk! It has been built mainly for testing purposes.")
    print(f"This script will encrypt the file {plain} and save it as {encrypted}.")

    with io.open(plain, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = data["db"]["entries"]

    db = AegisDB(encrypted, "test")
    db.encrypt(entries)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
