# Aegis-decrypt
A backup decryptor and OTP generator for the vault of the [Aegis Authenticator](https://github.com/beemdevelopment/Aegis/) Android app, inspired by [asmw/andOTP-decrypt](https://github.com/asmw/andOTP-decrypt). It allows to decrypt the Aegis vault and export its values in different formats (stdout, CSV, QRCode, Json). It allows to generate TOTP codes on the fly.

:warning: Currently, it supports only TOTP tokens.
:warning: A few improvements are in progress:
- export QRCodes in a unique PDF or HTML (simple paper backup)
- support for HOTP format

[![](https://img.shields.io/static/v1?label=Gitlab&message=Aegis-decrypt&style=for-the-badge&logo=gitlab)](https://gitlab.com/scollovati/Aegis-decrypt)
[![](https://img.shields.io/static/v1?label=Codeberg&message=Aegis-decrypt&style=for-the-badge&logo=codeberg)](https://codeberg.org/scollovati/Aegis-decrypt)
[![](https://img.shields.io/static/v1?label=Github&message=Aegis-decrypt&style=for-the-badge&logo=github)](https://github.com/scollovati/Aegis-decrypt)
## Usage
```
python3 aegis_decrypt.py [-h] --vault VAULT [--entryname ENTRYNAME] [--issuer ISSUER] [--output {None,csv,qrcode,json,otp}] [--password PASSWORD]
```
Exports are created in the folder `./export/` inside the project itself

## Development Setup

- Install [Poetry](https://python-poetry.org/docs/#installation)  (recommended)
- Install the package: `poetry install`
- Run the program : `poetry run python aegis_decrypt.py`
- Update dependencies: `poetry update`
- Execute Bandit `poetry run bandit -c pyproject.toml -r .`
- Execute Black `poetry run black .`
- Execute MyPy `poetry run mypy .`
- Execute Pylint `poetry run pylint .`

## Project Management
Since this repo is spread across several remotes, it may happen that there are some pull/merge request need to be handled locally.
- Add the remote repository URL with a meaningful NAME: `git remote add NAME URL `
- Create a local BRANCH name from the GitHub pull request ID: `git fetch origin pull/$ID/head:$BRANCHNAME`

## Contributors
- [asmw](https://github.com/asmw): original andOTP-decrypt repository on GitHub
- [scollovati](https://gitlab.com/scollovati/): forked andOTP-decrypt and setup the Aegis-decrypt project
- [kvngvikram](https://github.com/kvngvikram)
- [combolek](https://github.com/combolek)