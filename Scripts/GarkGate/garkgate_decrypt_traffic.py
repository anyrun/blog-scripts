# Example of an encrypted message
message = "g2JXedWrPu6X9mUUR0W0eIiA9mU6gmiA9mKr9mP0Rd9N9UH5GITD9U11S4TZuXH5G06D9U11S4TZ9iH5GLJD9U65S4TnuUH5G0cD9UNAS4TZ9iH5G06D9UFtS4TH9XH5Q4qr9icFSRseEF9Fp0HN9PgbQC" 
# Custom Base64 alphabet 
custom_alphabet = "zLAxuU0kQKf3sWE7ePRO2imyg9GSpVoYC6rhlX48ZHnvjJDBNFtMd1I5acwbqT+=" 

def base64_decode_custom(encoded_text):
    decoded_text = ""
    bits = ""

    for char in encoded_text:
        value = custom_alphabet.index(char)
        bits += format(value, '06b')  
    
    while len(bits) % 8 != 0:
        bits = bits[:-1]
    
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        decoded_text += chr(int(byte, 2))
    
    return decoded_text

def key_encode(key):
    
    enc_key = ''
    length = len(key) 
    for i in range(length):
        enc_key += chr((length-i)^ord(key[i]))
    
    return enc_key

def decode_message(text,key):
    
    n = 0
    key_char = key[0]
    decode_text = chr(text[0] ^ key_char)
    
    for i in range(1,len(text)):
        
        n = (n + key_char) % 0x20
        key_char = key[n]
        decode_text += chr(text[i] ^ key_char)
    
    return(decode_text)

decoded_base = base64_decode_custom(message)
key = decoded_base[:32]
enc_text = decoded_base[32:]

enc_key = key_encode(key)
print(decode_message(enc_text.encode(), enc_key.encode()))
