# Razr Ransomware Decryptor Script

This script is specifically designed to decrypt files that have been encrypted by the Razr ransomware. To successfully decrypt these files, you will need a JSON file containing the encryption key and initialization vector (IV), which can be extracted from the network traffic during the encryption process.

## Prerequisites

- **Python 3.x**
- **`pycryptodome`** package (used for AES encryption and SHA-256 hashing)

### Install the required package:

To install the `pycryptodome` package, run:

```bash
pip install pycryptodome
```

## Usage

```bash
python razr_decrypt.py <encrypted_file> <json_file>
```

## Output

- Upon successful decryption, the decrypted file will be saved in the same directory as the encrypted file. The output file will have the same name as the encrypted file but without the `.raz` extension. If the encrypted file does not have a `.raz` extension, the decrypted file will be named by appending `.decrypted` to the original filename.
