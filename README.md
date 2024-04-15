# Aegis-decrypt
A backup decryptor for the [Aegis](https://github.com/beemdevelopment/Aegis/) Android app, inspired by [asmw/andOTP-decrypt](https://github.com/asmw/andOTP-decrypt).

:warning: A few improvements, like `CSV` export are in progress.

[![](https://img.shields.io/static/v1?label=Gitlab&message=Aegis-decrypt&style=for-the-badge&logo=gitlab)](https://gitlab.com/scollovati/Aegis-decrypt)
[![](https://img.shields.io/static/v1?label=Github&message=Aegis-decrypt&style=for-the-badge&logo=github)](https://github.com/scollovati/Aegis-decrypt)
## Usage
```
python3 aegis-decrypt.py [-h] --vault VAULT [--entryname ENTRYNAME] [--output {None,csv,qrcode,json,otp}]
```
Exports are created in the folder `./export/` inside the projecy itself
## Installation

`pip install andotp-decrypt`

The tools will be installed as:

- `andotp_decrypt`
- `andotp_gencode`
- `andotp_qrcode`

## Development Setup

[Pipenv](https://pipenv.pypa.io/) install (recommended)

- Install poetry
  - `pip install --user pipenv` (or use the recommended way from the website)
- Install everything else
  - `pipenv install`
- Launch the virtualenv
  - `pipenv shell`

Pip install

- `pip3 install --user -r requirements.txt` 

## Usage

- Dump JSON to the console:
  - `./andotp_decrypt.py /path/to/otp_accounts.json.aes`
- Generate new QR codes:
  - `./generate_qr_codes.py /path/to/otp_accounts.json.aes`
- Generate a TOTP code for your google account:
  - `./generate_code.py /path/to/otp_accounts.json.aes google`
