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

from triton import *  

code = [
 
(0x97DF01, b"\xBA\x58\x34\xF1\xB5"),                          # mov edx,B5F13458 
(0x97DF06, b"\xC7\x85\xD0\xFC\xFF\xFF\x57\xAC\x5E\x0E"),      # mov dword ptr ss:[ebp-330],E5EAC57 
(0x97DF10, b"\x89\x95\xD4\xFC\xFF\xFF"),                      # mov dword ptr ss:[ebp-32C],edx
(0x97DF16, b"\xB8\xAD\xF2\x29\xA9"),                          # mov eax,A929F2AD 
(0x97DF1B, b"\xC7\x85\xD8\xFC\xFF\xFF\xE0\x15\xFD\xB3"),      # mov dword ptr ss:[ebp-328],B3FD15E0
(0x97DF25, b"\x89\x85\xDC\xFC\xFF\xFF"),                      # mov dword ptr ss:[ebp-324],eax 
(0x97DF2B, b"\xB9\x6D\x00\xDF\x87"),                          # mov ecx,87DF006D 
(0x97DF30, b"\xC7\x85\xD0\xE3\xFF\xFF\x65\x9F\x70\x3C"),      # mov dword ptr ss:[ebp-1C30],3C709F65
(0x97DF3A, b"\x89\x8D\xD4\xE3\xFF\xFF"),                      # mov dword ptr ss:[ebp-1C2C],ecx
(0x97DF40, b"\xBA\x9C\xC6\x29\xA9"),                          # mov edx,A929C69C
(0x97DF45, b"\xC7\x85\xD8\xE3\xFF\xFF\xD2\x22\xD3\x81"),      # mov dword ptr ss:[ebp-1C28],81D322D2
(0x97DF4F, b"\x89\x95\xDC\xE3\xFF\xFF"),                      # mov dword ptr ss:[ebp-1C24],edx
(0x97DF55, b"\x33\xC0"),                                      # xor eax,eax
(0x97DF57, b"\x88\x85\xDA\xF4\xFF\xFF"),                      # mov byte ptr ss:[ebp-B26],al 
(0x97DF5D, b"\x8A\x8D\xDA\xF4\xFF\xFF"),                      # mov cl,byte ptr ss:[ebp-B26] 
(0x97DF63, b"\x88\x8D\xD4\xEE\xFF\xFF"),                      # mov byte ptr ss:[ebp-112C],cl 
(0x97DF69, b"\x0F\x28\x85\xD0\xE3\xFF\xFF"),                  # movaps xmm0,xmmword ptr ss:[ebp-1C30]
(0x97DF70, b"\x0F\x29\x85\x10\xD3\xFF\xFF"),                  # movaps xmmword ptr ss:[ebp-2CF0],xmm0
(0x97DF77, b"\x0F\x28\x85\xD0\xFC\xFF\xFF"),                  # movaps xmm0,xmmword ptr ss:[ebp-330]
(0x97DF7E, b"\x0F\x29\x85\xC0\xD5\xFF\xFF"),                  # movaps xmmword ptr ss:[ebp-2A40],xmm0
(0x97DF85, b"\x0F\x28\x85\xC0\xD5\xFF\xFF"),                  # movaps xmm0,xmmword ptr ss:[ebp-2A40]
(0x97DF8C, b"\x66\x0F\xEF\x85\x10\xD3\xFF\xFF"),              # pxor xmm0,xmmword ptr ss:[ebp-2CF0]
(0x97DF94, b"\x0F\x29\x85\x00\xD3\xFF\xFF"),                  # movaps xmmword ptr ss:[ebp-2D00],xmm0 
(0x97DF9B, b"\x0F\x28\x85\x00\xD3\xFF\xFF"),                  # movaps xmm0,xmmword ptr ss:[ebp-2D00]
(0x97DFA2, b"\x0F\x29\x85\xD0\xFC\xFF\xFF"),                  # movaps xmmword ptr ss:[ebp-330],xmm0
(0x97DFA9, b"\x8D\x95\xD0\xFC\xFF\xFF"),                      # lea edx,dword ptr ss:[ebp-330]

]

if __name__ == '__main__':

    Triton = TritonContext()

    #Set the arch
    Triton.setArchitecture(ARCH.X86)
   
    Triton.setConcreteRegisterValue(Triton.registers.ebp, 0x5000)
    Triton.setConcreteRegisterValue(Triton.registers.esp, 0x5000)

    for (addr, opcode) in code:
    
        # Build an instruction
        inst = Instruction(addr, opcode)

        # Process everything
        Triton.processing(inst)
      
    edx = Triton.getConcreteRegisterValue(Triton.registers.edx)
    value = Triton.getConcreteMemoryAreaValue(edx, 16)
    
    #decode strings
    string = {'Decode string:':value.decode().rstrip('\0')}  
    print(string)

   

