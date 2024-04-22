from triton import TritonContext, ARCH, Instruction , OPCODE , OPERAND, EXCEPTION
import sys


# GuLoader takes the value relative to the address where the exception occurred. Offset to this
# value can be found using this string (YARA syntax):
#                           {01 d0 [0-10] 8b 10 [0-10] 83 c2} 
offet_to_next_instr = 0x4

# To decrypt the given offset, we need to XOR it with a constant key. To find the key you may use 
# the following string (YARA syntax), which works with all the recent Guloader versions:
#                       {39 48 14 (75 | 0f) [1-5] [0-10] 39 48 18 (75 | 0f) [1-5] [0-10] b9}
veh_xor_key = 0x9b

# Handles exceptions by computing a new instruction pointer (EIP) based on XOR operations.
def veh_handler(old_eip):
    xored_value = ctx.getConcreteMemoryValue(old_eip + offet_to_next_instr)
    xor_result = xored_value ^ veh_xor_key
    new_eip = xor_result + old_eip
    return new_eip

# Checks if the instruction accesses invalid memory, based on predefined memory regions.
def check_access_to_invalid_mem(inst):

    if inst.isMemoryRead() == False and inst.isMemoryWrite() == False:
        return False
    operands = inst.getOperands()
    if len(operands) == 0:
        return False
    for op in operands:
        if op.getType() != OPERAND.MEM:
            continue
        addr = op.getAddress()
        if addr >= stack_end and addr <= stack_begin:
            continue
        elif addr >= base_address and addr <= base_address + data_size:
            continue
        elif addr >= heap_address and addr <= heap_address + heap_size:
            continue
        else:
            return True

    return False

# Retrieves the mnemonic part of the disassembled instruction.
def get_mnem( inst):
    inst_disass = inst.getDisassembly()
    without_addr = inst_disass.split(": ")[0]
    return without_addr

# Updates the Virtual IP (VIP) based on exception status and handled conditions.
def update_vip(vip, status, inst):

    global popfd_detected

    priv_instr = [OPCODE.X86.WBINVD, OPCODE.X86.CLTS, OPCODE.X86.STC, OPCODE.X86.LGDT, 
                OPCODE.X86.LIDT, OPCODE.X86.LLDT, OPCODE.X86.LMSW, OPCODE.X86.LTR, 
                OPCODE.X86.RDMSR, OPCODE.X86.SYSRET, OPCODE.X86.INVD]

    # Exceptions:
    # 1. Exceptions that Triton can handle
    # 2. Priviliged instruction exception
    # 3. Single-step exception
    if  status != EXCEPTION.NO_FAULT or \
            check_access_to_invalid_mem(inst) or \
            inst.getType() in priv_instr or \
            popfd_detected == True and get_mnem(inst)[0] == 'j':

        popfd_detected = False
        vip = veh_handler(vip)
    else:
        # If there are no exceptions:
        vip = ctx.getConcreteRegisterValue(ctx.registers.eip)

    return vip

# Finds the length of the cyphertext within data, terminating at double NULL bytes.
def get_cyphertext_len( data):
    end = data.find(b"\x00\x00")
    if end == -1:
        return 0
    return end

# Fetches cyphertext by executing code until a specific instruction or condition is met.
def get_cyphertext():
    vip = base_address + offset_to_cyphertext_dropper

    ctx.setConcreteMemoryAreaValue(stack_pointer + 4, heap_address.to_bytes(4, "little"))
    instr_counter = 0

    global popfd_detected
    popfd_detected = False

    for i in range(6000):

        opcodes = ctx.getConcreteMemoryAreaValue(vip, 16)
        if opcodes[:4] == b"\x00\x00\x00\x00":
            break
        inst = Instruction(vip, opcodes)
        status = ctx.processing(inst)

        if inst.getType() == OPCODE.X86.RET:
            break
        if inst.getType() == OPCODE.X86.POPFD:
            popfd_detected = True
        
        vip = update_vip(vip, status, inst)
        instr_counter+=1

    global cyphertext_len

    if cyphertext_len > 0x1000:
        return False
    cyphertext_data = ctx.getConcreteMemoryAreaValue(cyphertext_buffer, cyphertext_buffer_size)

    cyphertext_len = get_cyphertext_len(cyphertext_data)

    return cyphertext_data

# Decrypts the fetched cyphertext using specified decryption procedures.
def decrypt():
    ctx.setConcreteRegisterValue(ctx.registers.eax, cyphertext_buffer)

    cyphertext_data = ctx.getConcreteMemoryAreaValue(cyphertext_buffer, cyphertext_buffer_size)
    ctx.setConcreteRegisterValue(ctx.registers.ebx, cyphertext_len)

    global popfd_detected
    instr_counter = 0

    vip = decrypt_func_offset + base_address
    for i in range(6000):
        opcodes = ctx.getConcreteMemoryAreaValue(vip, 16)
        inst = Instruction(vip, opcodes)
        ctx.processing(inst)

        if inst.getType() == OPCODE.X86.RET or opcodes[:4] == b"\x00\x00\x00\x00":
            break

        vip = ctx.getConcreteRegisterValue(ctx.registers.eip)

        instr_counter+=1

    cyphertext_data = ctx.getConcreteMemoryAreaValue(cyphertext_buffer, cyphertext_len)
    
    return cyphertext_data


ctx = TritonContext()
ctx.setArchitecture(ARCH.X86)

guloader_dmp = open("guloader.dmp", "rb")
data = guloader_dmp.read()

decrypt_func_offset = 0xdfa086

data_size           = len(data)

base_address        = 0x10000000
stack_begin         = 0x50000000
stack_pointer       = 0x45000000
stack_end           = 0x40000000
heap_address        = 0x30000000

heap_size               = 0x1000
cyphertext_buffer_size  = 0x1000
popfd_detected          = False # for handling single-step exceptions
cyphertext_buffer       = heap_address + 4
cyphertext_len          = 0


offset_to_cyphertext_dropper = int(sys.argv[1], 16)
ctx.setConcreteMemoryAreaValue(base_address, data)
ctx.setConcreteRegisterValue(ctx.registers.ebp, stack_pointer)
ctx.setConcreteRegisterValue(ctx.registers.esp, stack_pointer)

cyphertext_data = get_cyphertext()
decrypted_data = decrypt()
print(decrypted_data)
