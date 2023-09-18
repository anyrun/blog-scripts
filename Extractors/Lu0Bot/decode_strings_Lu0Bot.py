import  re, base64, malduck, sys

def Decode_Base64(string):
    
    base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    custom = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/"

    string = string.translate(str.maketrans(custom, base))
    decoded = base64.b64decode(string)
    
    return decoded

def Decode_to_Hex(string):
    
    byte = ""
    for b in string:
        if len(hex(ord(b))[2:]) == 1:
            byte += "0" + hex(ord(b))[2:]
        else:
            byte += hex(ord(b))[2:]
            
    return byte

def Decode_Strings(sample, output):
     
    with open(sample) as file:
        string = file.read() 
        
    start_list = re.match("var \_0x[a-z0-9]{4}\=\[", string).end()
    enc_strings = (string[start_list:].split("]",1)[0]).split(",") #list of enc string

    MOVE_REGEX = "0x[a-f0-9]{4,6}\(\+\+\_0x[a-f0-9]{4,6}\);}\(\_0x[a-f0-9]{4,6}\,0x"
    NUMBER_SUB_REGEX = "{\_0x[a-f0-9]{4,6}=\_0x[a-f0-9]{4,6}-"

    move_pos = re.search(MOVE_REGEX, string).end()
    nuber_sub_pos = re.search(NUMBER_SUB_REGEX, string).end()

    move = int(string[move_pos:].split(")",1)[0],16)
    nuber_sub = int(string[nuber_sub_pos:].split(";",1)[0],16)

    #Working with an array (move to the end)
    for i in range(move):
        enc_strings.append(enc_strings[0])
        enc_strings.pop(0)
    position = {}
    all_str = []
    
    #decode part
    for i in re.finditer("\_0x[a-z0-9]{6}\(0x[a-z0-9]{2,4}\,\'[\w\W]{4}\'\)", string):
        
        index = i.group()[10:].split(",",1)[0]
        index = int(index,16) - nuber_sub

        key = i.group().split(",",1)[1][1:5].encode("ascii")
        enc_string = enc_strings[index].replace("'","")

        dec_string = Decode_Base64(enc_string)

        byte = Decode_to_Hex(dec_string.decode())
            
        string_decode = malduck.rc4(key,bytes.fromhex(byte))
        
        position[string[i.start():i.end()]] = string_decode.decode()
        all_str.append(string_decode.decode())

    for key in position.keys():
        if len(position[key]) > 10000:
            BASE64 = position[key]
            string = string.replace(key,"'"+"LARGE BASE"+"'")
        else:
            string = string.replace(key, repr(position[key]))

    deobf_code = open(output + "decoded_code.js", "w+")
    deobf_code.write(string)
    deobf_code.close()
    
    base = open(output + "base64_large.txt", "w+")
    base.write(BASE64)
    base.close()

def main():
    
    if len(sys.argv) < 3:
        print ("[!] usage: python decode_strings_Lu0Bot.py <path_file> <folder_output>")
        return
    
    SAMPLE = sys.argv[1] 
    OUTPUT = sys.argv[2]
    
    Decode_Strings(SAMPLE, OUTPUT)
        
if __name__ == "__main__":
    main()