# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, random, re
from pathlib import Path

SIGNATURE = b"\x50\x4B\x03\x04"  # Original ZIP signature
FAKE_SIGNATURE = b"\x50\x4B\xC3\x90\xC3\x8F"
END_SIGNATURE = b"\x20\x7D\xCE\x99"
BYTES_GENERATE = [bytes([i]) for i in range(256)]
ALLOWED_EXTENSIONS = {'.docx', '.xlsx', '.zip'}

def generate_corrupt(file_data: bytes, filename: str) -> bool:
    try:
        # Create corrupted signature
        corrupted_bytes = FAKE_SIGNATURE + b''.join(random.choice(BYTES_GENERATE) for _ in range(1000)) + END_SIGNATURE
        
        output_path = Path(f"broken_{filename}")
        with open(output_path, "wb") as f:
            f.write(corrupted_bytes + file_data)
            
        print(f"[+] Generated corrupted file: {output_path}")
        return True

    except Exception as e:
        print(f"[-] Generation failed: {str(e)}")
        return False

def fix_corrupt(file_data: bytes, filename: str) -> bool:
    try:
        offset_signature = re.search(SIGNATURE, file_data).start()
        
        if offset_signature == 0:
            print("[-] File is not corrupted!")
            return False
        
        output_path = Path(f"fixed_{filename}")
        fixed_bytes = file_data[offset_signature:]
        
        with open(output_path, "wb") as f:
            f.write(fixed_bytes)

        print(f"[+] Fixed file saved as: {output_path}")
        return True 
        
    except AttributeError:
        print("[-] Original signature not found in file")
        return False
    except Exception as e:
        print(f"[-] Fix failed: {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("[!] Usage: python check.py <path to docx/xlsx/zip file>")
        return
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"[-] File not found: {input_path}")
        return
        
    if input_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        print(f"[-] Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
        return

    try:
        # Read input file
        file_data = input_path.read_bytes()
        
        # Get user choice
        print("\nChoose operation:")
        print("1. Generate corrupted file")
        print("2. Fix corrupted file")
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            if generate_corrupt(file_data, input_path.name):
                print("[+] File corruption completed successfully!")
        elif choice == "2":
            if fix_corrupt(file_data, input_path.name):
                print("[+] File fixed successfully!")
        else:
            print("[-] Invalid choice!")
        
    except Exception as e:
        print(f"[-] Error during processing: {str(e)}")

if __name__ == "__main__":
    main()
