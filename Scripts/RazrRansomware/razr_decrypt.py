import json
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import sys
import binascii
import os

def decrypt_file(encrypted_file, json_file):
    # Read the JSON file with iv and key data
    with open(json_file, 'r') as f:
        data = json.load(f)
        key_hex = data['key']
        iv_hex = data['iv']

    # Convert key and IV from HEX format to bytes
    key = binascii.unhexlify(key_hex)
    iv = binascii.unhexlify(iv_hex)

    # Generate derived key using SHA-256
    hasher = SHA256.new()
    hasher.update(key)
    derived_key = hasher.digest()  # get a 32-byte (256-bit) key

    # Read the encrypted file
    with open(encrypted_file, 'rb') as f:
        encrypted_data = f.read()

    # Initialize AES object for decryption in CBC mode
    cipher = AES.new(derived_key, AES.MODE_CBC, iv)

    # Decrypt the data
    decrypted_data = cipher.decrypt(encrypted_data)

    # Remove padding (if it was added)
    padding_len = decrypted_data[-1]
    decrypted_data = decrypted_data[:-padding_len]

    # Create decrypted file name by removing '.raz' extension
    if encrypted_file.endswith('.raz'):
        decrypted_file = encrypted_file[:-4]  # Remove '.raz'
    else:
        decrypted_file = encrypted_file + '.decrypted'  # Fallback if no .raz extension

    # Save the decrypted file
    with open(decrypted_file, 'wb') as f:
        f.write(decrypted_data)

    print(f"File successfully decrypted as {decrypted_file}!")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python razr_decrypt.py <encrypted_file> <json_file>")
        sys.exit(1)

    encrypted_file = sys.argv[1]
    json_file = sys.argv[2]

    decrypt_file(encrypted_file, json_file)
