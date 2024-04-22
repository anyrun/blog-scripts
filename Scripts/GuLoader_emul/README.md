#### GuLoader emulation example
This python script is an example of how you can emulate GuLoader for strings and C2 decryption.</br>
There is also a YARA rule here that can help you find the right offsets for emulation.</br>
To use the script you need to install Triton.</br>
##### Triton installation:
Here's a guide: https://github.com/JonathanSalwan/Triton?tab=readme-ov-file#install</br>
##### The sample used in the example:
SHA256: 3b0b1b064f6b84d3b68b541f073ddca759e01adbbb9c36e7b38e6707b941539e</br>
https://app.any.run/tasks/aabc765a-ff14-4e8f-902b-75ae29809d1f</br>
An archive containing the process dump is available in the current repository. Use the password `infected` to open it</br>
##### How to run:
`python3 GuLoader_emul.py filename.dmp <function_with_cyphertext>`
##### Usage example:
`python3 GuLoader_emul.py guloader.dmp 0xdf5a13`<br/>
0xdf5a13 - offset to the function that generates cyphertext for string.</br>
guloader.dmp - dump with decrypted shellcode.</br>
output: `b'ApposLevadamkiddoo.com/ASsHdVpRUDfpWtkNHm150.bin\x00'`