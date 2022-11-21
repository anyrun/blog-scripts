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

import re, sys, malduck	


class CryptBotExtractor:
    
    def __init__(self, file_dump: str):
        self.file_dump = file_dump

    def Extract(self) -> dict:
        
        file_dump = self.file_dump
        
        with open(file_dump,'rb') as byt:
            data = byt.read()
        
        regex = re.search(b'\x00http://', data)
        if regex != None: 
            offset = regex.start()
            cfg = self.__parse_config(data, offset+1, 0)
        else:
            key,offset = self.__brute_force_key(data)
            cfg = self.__parse_config(data, offset, key)
            
        return cfg
        
    def __brute_force_key(self,data):
            
        MIN_LEN = 7
        MAX_LEN = 12
            
        reg = f'[\d\w]{{{MIN_LEN},{MAX_LEN}}}'
        coincidences = re.compile(bytes(reg, 'utf-8')+b'\x00')
        
        for match in coincidences.finditer(data):
            
            key =  data[match.start():match.end()-1]
            offset_data = match.end()
            data_XOR = data[offset_data:offset_data + 4]
                
            for i in range(MAX_LEN-MIN_LEN):
                    
                key_XOR = key[i:]
                data_dec = malduck.xor(key_XOR,data_XOR)
                    
                if data_dec == b'http':
                        return key_XOR, offset_data
                else:
                    continue 

    def __parse_config(self,data,offset,key):
            
        if key == 0:
                data_dec = data[offset:].split(b'\x00\x5f\x78', 1)[0]
        else:
            data_XOR = data[offset:].split(b'\x00'*4, 1)[0]
            data_dec = malduck.xor(key,data_XOR)
            
        dic_parse = {}
        options = {}
            
        dic_parse["C2"], conf = data_dec.split(b'\0', 1)
        dic_parse["C2"] = str(dic_parse["C2"], 'UTF-8')

        conf = str(conf,'UTF-8').split('<>\r\n')
            
        for i in range(len(conf)-1):

            key,value = conf[i].split('<>_<>', 1)
            options[key.lstrip('\x00')] = value.lstrip('\x00')
                
        dic_parse["Options"] = [options]
            
        return dic_parse
        
def main():
    
    if len(sys.argv) < 2:
        print ("[!] usage: python script.py <sample path>")
        return
        
    file_dump = sys.argv[1]
    
    config = CryptBotExtractor(file_dump).Extract()
    print(config)
      
        
if __name__ == "__main__":
    main()
