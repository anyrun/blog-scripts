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

import re, malduck, sys

def Parse_Config(data,offset):
      
    l = malduck.u32(data,(offset-2))
    data_res = str(data[offset:l+offset].lstrip(b'\x00'), 'UTF-8')
    values = data_res.split('|')
    dic_parse = {}
    dic_parse["C2"] = values[0]
    dic_parse["Port"] = values[1]
    dic_parse["URL"] = values[2]
    dic_parse["Options"] = [
        {
            "Startup" : values[5],
            "Secondary Startup" : values[6],
            "Scheduled Task" : values[7],
            "Proxy" : values[3],
            "LID" : values[-1]
            }
        ]

    return dic_parse

def main():
    
    if len(sys.argv) < 2:
        print ("[!] usage: python script.py <sample path>")
        return
        
    file_dump = sys.argv[1]
        
    with open(file_dump,'rb') as byt:
        data = byt.read()
    
    regex = re.search(b'\x00\x00([\d\w-]{1,60}(\.)?){1,4}\|[\d]{2,4}\|http', data)
    offset = regex.start()
    cfg = Parse_Config(data, offset)
    
    print(cfg)
        
if __name__ == "__main__":
    main()

