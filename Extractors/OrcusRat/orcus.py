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

# please, check out README.md before using this

import dnfile, base64, hashlib, json, sys, os, xml.etree.ElementTree as ET
from malduck import enhex, unpad
from enum import IntEnum
from Crypto.Cipher import AES

class EOrcusCfgEntry(IntEnum):
    PROPERTIES = 0,
    PROPERTY_NAME_VALUE = 0,
    PLUGIN_RESOURCE_NAME = 0,
    KEY = 0,
    IP = 0,
    PORT = 1,
    VALUE = 1,
    PLUGIN_RESOURCE_TYPE = 1,
    PLUGIN_GUID = 2,
    PLUGIN_NAME = 3,
    PLUGIN_VERSION = 4

class OrcusDecryptor:
    def __init__(self, sample_path) -> None:
        with open(sample_path, 'rb') as bin:
            self.buffer = bin.read()

        cfg_raw_data = self.__get_cfg_raw_data(self.buffer)
        self.config_main = base64.b64decode(cfg_raw_data[0])
        self.config_plugins = base64.b64decode(cfg_raw_data[1])
        self.aes_key = self.__pbkdf1(cfg_raw_data[2].encode(), b"")

        # iv is hardcoded in orcus packed resources and doesn't seem to vary from sample to sample
        self.aes_iv = bytes("0sjufcjbsoyzube6", encoding="ascii") 

    def decrypt_main_cfg(self) -> dict:
        cfg = unpad(
            AES.new(
                self.aes_key, AES.MODE_CBC, self.aes_iv
            ).decrypt(self.config_main)
        ).decode()
        return self.__parse_main_cfg(cfg)

    def decrypt_plugins_cfg(self) -> dict:
        raise NotImplementedError() # todo

    def __get_cfg_raw_data(self, data) -> list: # parse .NET executable
        dn = dnfile.dnPE(data=data)
        if not hasattr(dn, "net"):
            ValueError("This is not a .NET executable")

        cfg_data = []
        should_collect_data = False
        us = dn.net.metadata.streams.get(b"#US", None)

        if us:
            size = us.sizeof()  # get the size of the stream
            offset = 1 # the first entry (the first byte in the stream) is an empty string, so skip it
           
            while offset < size: # while there is still data in the stream
                # read the raw string bytes, and provide the number of bytes to read (includes the encoded length)
                ret = us.get_with_size(offset)
                if ret is None:
                    break

                buf, readlen = ret

                try:
                    s = dnfile.stream.UserString(buf) # convert data to a UserString object

                    if "klg_" in s.value: break # hit an encapsulating string, leaving..
                        
                    if should_collect_data: # collect everything between reference strings
                        cfg_data.append(s.value)

                    if s.value == "case FromAdministrationPackage.GetScreen":
                        should_collect_data = True # we should collect data starting from this line

                except UnicodeDecodeError:
                    raise ValueError(f"Bad string: {buf}")

                offset += readlen  # continue to the next entry

        if len(cfg_data) != 3:
            raise ValueError("Got invalid cfg data")

        return cfg_data

    def __parse_main_cfg(self, cfg) -> dict:
        result = {
            "C2": [],
            "Keys": [{ 
                "AES": enhex(self.aes_key).decode(),
                "Salt": ""
            }],
            "Options": [
                {},
                {"Plugins": []}
            ]
        } # basic config layout

        def parse_cfg_property(xml_el: ET.Element, property: ET.Element) -> None:
            if property[EOrcusCfgEntry.KEY].text == "IpAddresses":
                # c2 is a special case cuz we need it outside of 'options'
                for c2 in property[EOrcusCfgEntry.VALUE]:
                    ip = c2[EOrcusCfgEntry.IP].text
                    port = c2[EOrcusCfgEntry.PORT].text
                    result["C2"].append(f"{ip}:{port}")
                return

            prop_parent = xml_el.attrib["SettingsType"].split(",")[0]

            # workaround: escaping dots symbols
            prop_parent = prop_parent.split(".")[-1]

            prop_key = property[EOrcusCfgEntry.KEY].text

            try: prop_value = property[EOrcusCfgEntry.VALUE].text
            except IndexError: prop_value = None

            if prop_parent not in result["Options"][0]:
                result["Options"][0][prop_parent] = {}

            result["Options"][0][prop_parent][prop_key] = prop_value

        xml_tree = ET.ElementTree(ET.fromstring(cfg))
        xml_root = xml_tree.getroot()

        for xml_entry in xml_root: # parsing xml tree
            if xml_entry.tag == "PluginResources":
                for xml_el in xml_entry:
                    result["Options"][1]["Plugins"].append({
                        "PluginName":    xml_el[EOrcusCfgEntry.PLUGIN_NAME].text,
                        "PluginVersion": xml_el[EOrcusCfgEntry.PLUGIN_VERSION].text,
                        "ResourceName":  xml_el[EOrcusCfgEntry.PLUGIN_RESOURCE_NAME].text,
                        "ResourceType":  xml_el[EOrcusCfgEntry.PLUGIN_RESOURCE_TYPE].text,
                        "Guid":          xml_el[EOrcusCfgEntry.PLUGIN_GUID].text
                    })

            elif xml_entry.tag == "Settings":
                for xml_el in xml_entry: 
                    for client_setting in xml_el:
                        for property in client_setting:
                            parse_cfg_property(xml_el, property)

        return result

    # microsoft's pbkdf1 implementation
    def __pbkdf1(self, password, salt, count=32, iterations=100) -> bytes: 
        def do_hash(data) -> bytes:
            _sha1 = hashlib.sha1()
            _sha1.update(data)
            data = _sha1.digest()
            return data

        if len(salt) > 0:
            password = password + salt

        for i in range(iterations - 1):
            password = do_hash(password)

        ret = do_hash(password)

        i = 1
        while len(ret) < count:
            ret += do_hash(bytes(str(i), encoding="ascii") + password)
            i += 1

        return ret[:count]

def main():
    # parse arguments
    if len(sys.argv) == 2:
        sample_path = os.path.abspath(sys.argv[1])
    else:
        print(f"[!] usage: {os.path.basename(__file__)} <sample path>")
        return False

    try:
        config = OrcusDecryptor(sample_path).decrypt_main_cfg()
        print(json.loads(json.dumps(config)))
    except Exception as ex:
        print(f"[!] exception: {ex}")

if __name__ == '__main__':
    main()