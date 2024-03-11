from ghidra.program.disassemble import Disassembler
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.program.model.address import Address, AddressSet
from ghidra.program.model.lang import OperandType
from ghidra.app.plugin.assembler import Assemblers
from ghidra.app.emulator import EmulatorHelper

import logging, Queue, array

LOG_FILENAME = 'log.txt'

class GuDeobfuscator:
    MAX_INSTR_DISM = 100

    def __init__(self, entry_point):
        """
        Initializes the GuDeobfuscator class with various attributes like program,
        addrFactory, listing, language, memory, monitor, asm, and disassembler.
        entry_point is the starting point of the guloader code that needs to be
        deobfuscated.
        """
        self.program = currentProgram
        self.addrFactory = self.program.getAddressFactory()
        self.listing = self.program.getListing()
        self.language = self.program.getLanguage()
        self.memory = self.program.getMemory()
        self.monitor = ConsoleTaskMonitor()

        self.asm = Assemblers.getAssembler(self.program)
        self.disassembler = Disassembler.getDisassembler(self.program, self.monitor, None)

        self.entry_point = entry_point
        self.next_block = Queue.Queue()

        self.cond_cache = None
        self.mov_opt = None
        self.pushad_opt = False
        self.push_opt = False

        self.__setupLogger()
        self.logger.info('Starting GuLoader deobfuscator at 0x{}...'.format(entry_point))

    def __setupLogger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.DEBUG)

        self.file_handler = logging.FileHandler(LOG_FILENAME, 'w')
        self.file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(message)s')
        self.console_handler.setFormatter(formatter)
        self.file_handler.setFormatter(formatter)

        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)

    def dismBlock(self, address):
        """
        Disassembles the block of code starting at the provided address.
        Returns a BlockModel object containing information about the disassembled block.
        """
        if not self.isUndefined(address):
            return None

        pseudo_dism = Disassembler.getDisassembler(self.program, self.monitor, None)
        block = pseudo_dism.pseudoDisassembleBlock(address, None, GuDeobfuscator.MAX_INSTR_DISM)
        if block.hasInstructionError():
            inst_err = block.getInstructionConflict()
            self.logger.critical(inst_err)
            raise ValueError(inst_err)

        return block

    def patchBytes(self, start_address, sz, val):
        """
        Patches sz bytes starting at start_address with the provided value.
        First, it clears any existing code units in that range and then sets the bytes
        at that location to the provided value.
        """
        self.listing.clearCodeUnits(start_address, start_address.add(sz-1), False)
        patch = array.array("B", [val] * sz)
        self.memory.setBytes(start_address, patch)

    def nopBytes(self, start_address, sz):
        """
        Replaces sz bytes starting at start_address with NOP instructions (0x90).
        Calls the patchBytes method internally to achieve this.
        """
        self.patchBytes(start_address, sz, 0x90)

    def nopInst(self, inst):
        """
        Replaces the given instruction with a NOP instruction.
        Calculates the length of the instruction and then calls nopBytes to replace the
        instruction with NOP instructions.
        """
        if inst != None:
            addr = inst.getAddress()
            sz = inst.getLength()
            self.nopBytes(addr, sz)
            self.dismCodeUnit(addr, sz - 1)

    def isXMM(self, inst):
        """
        Checks whether the given instruction contains an XMM register.
        Returns True if it contains an XMM register, False otherwise.
        """
        mnemonic = inst.getMnemonicString()
        if mnemonic.startswith('PUSH') or mnemonic.startswith('POP'):
            return False

        if mnemonic.startswith('F') or mnemonic.startswith('P'):
            return True

        for i in range(inst.getNumOperands()):
            t = inst.getOperandType(i)
            if t & OperandType.REGISTER:
                reg = inst.getRegister(i)
                if reg.getName().startswith(('XMM', 'FPU', 'MM', 'ST')):
                    return True

        return False

    def isBlackListed(self, inst):
        """
        Checks whether the given instruction is a blacklisted instruction. Blacklisted
        instructions are not used by guloader. The method checks whether the instruction
        contains any of the blacklisted mnemonics like 'FENCE', 'WAIT', 'NOP', 'EMM',
        or whether it is an 'AND' or 'XCHG' instruction where the operands are the same or
        whether it is a 'MOV' instruction where the second operand is 0.
        """
        mnemonic = inst.getMnemonicString()
        if 'FENCE' in mnemonic or 'WAIT' in mnemonic \
            or 'NOP' in mnemonic or 'EMM' in mnemonic:
                return True

        # and eax, eax
        if mnemonic in ('AND', 'XCHG'):
            if inst.getOpObjects(0) == inst.getOpObjects(1):
                return True

        # mov REG, 0x0
        numOperands = inst.getNumOperands()
        if mnemonic != 'CMP' and numOperands == 2:
            if inst.getOperandType(0) & OperandType.REGISTER \
                and inst.getOperandType(1) & OperandType.SCALAR:
                    if inst.getOpObjects(1)[0].getValue() == 0:
                        return True

    def isFakeCond(self, inst):
        """
        Checks whether the given instruction is a fake conditional instruction.
        If the previous instruction was a comparison instruction like 'CMP', 'OR', or 'TEST',
        then the current instruction is considered fake conditional.
        """
        mn = inst.getMnemonicString()
        COMP_LIST_INST = ['CMP', 'OR', 'TEST']
        if mn in COMP_LIST_INST and self.cond_cache:
            return True

        return False

    def isConditionalJump(self, inst):
        """
        Checks whether the given instruction is a conditional jump instruction.
        """
        flowType = inst.getFlowType()
        return flowType.isJump() and flowType.isConditional()

    def isUnConditionalJump(self, inst):
        """
        Checks whether the given instruction is an unconditional jump instruction.
        """
        flowType = inst.getFlowType()
        return flowType.isJump() and flowType.isUnConditional()

    def isCall(self, inst):
        """
        Checks whether the given instruction is a call instruction.
        """
        flowType = inst.getFlowType()
        return flowType.isCall()

    def isChangeFlow(self, inst):
        """
        Checks whether the given instruction changes the control flow of the program.
        """
        return not inst.getFlowType().isFallthrough()

    def isFakePushAD(self, inst):
        """
        Checks whether the given instruction is a fake PUSHAD instruction.
        If the instruction is a PUSHAD, then it sets the pushad_opt flag to True.
        If the instruction is a POPAD and the pushad_opt flag is True, then it returns True.
        This indicates that the POPAD instruction is fake.
        """
        mn = inst.getMnemonicString()
        if mn == 'PUSHAD':
            print('PUSHAD: {}: {}'.format(inst.getAddress(), inst))
            self.pushad_opt = True
            return True
        if mn == 'POPAD' and self.pushad_opt:
            self.pushad_opt = False
            return True

        return self.pushad_opt

    def isFakePush(self, inst):
        """
        Checks whether the given instruction is a fake PUSH instruction.
        If the instruction is a PUSH and its operand is a register with a 2-letter name
        (like cx, dx), then it sets the push_opt flag to True.
        If the instruction is a POP and the push_opt flag is True, then it returns True.
        This indicates that the POP instruction is fake.
        """
        mn = inst.getMnemonicString()
        if mn == 'PUSH' and inst.getOperandType(0) & OperandType.REGISTER:
            op_name = inst.getOpObjects(0)[0].getName()
            if len(op_name) == 2: # like cx, dx
                #print('PUSH: 0x{}: {}'.format(inst.getAddress(), inst))
                self.push_opt = True
                return True

        if mn == 'POP' and self.push_opt:
            op_name = inst.getOpObjects(0)[0].getName()
            assert len(op_name) == 2

            #print('POP: 0x{}: {}'.format(inst.getAddress(), inst))
            self.push_opt = False
            return True

        return self.push_opt

    def isJUNK(self, inst):
        """
        Checks whether the given instruction is junk.
        If the instruction involves XMM registers, is blacklisted,
        is a fake PUSHAD or a fake PUSH instruction, it returns True.
        """
        return self.isXMM(inst) or self.isBlackListed(inst) \
            or self.isFakePushAD(inst) or self.isFakePush(inst)

    def getJumptarget(self, instr):
        """
        Given an instruction, returns the address of the target of the instruction, if any.
        """
        for i in range(instr.getNumOperands()):
            op = instr.getOpObjects(i)[0]
            if isinstance(op, Address):
                return op
        return None

    def isUndefined(self, addr):
        """
        Checks whether the given address is undefined in the current program.
        """
        return self.listing.isUndefined(addr, addr)

    def addNewTarget(self, inst):
        """
        Given an instruction, adds any new target addresses to the next_block queue.
        """
        if self.isUnConditionalJump(inst) or self.isConditionalJump(inst) or self.isCall(inst):
            target = self.getJumptarget(inst)
            if target and self.isUndefined(target):
                self.next_block.put(target)

            if (self.isCall(inst) and not target) or self.isConditionalJump(inst):
                next_addr = inst.getAddress().add(inst.getLength())
                if self.isUndefined(next_addr):
                    self.next_block.put(next_addr)

    def isComparison(self, inst):
        """
        Checks whether the given instruction is a comparison instruction.
        """
        mn = inst.getMnemonicString()
        return mn in ('CMP', 'TEST', 'CLD', 'CLC')

    def isChangeZf(self, inst):
        """
        Checks whether the given instruction changes the ZF flag.
        """
        mn = inst.getMnemonicString()
        return mn in ('INC', 'DEC')

    def filter(self, inst):
        """
        Given an instruction, applies a series of filters to it to determine whether to
        optimize it, remove it, or leave it as is.
        """
        if self.isJUNK(inst):
            self.nopInst(inst)
            return True

        if not self.cond_cache and self.isComparison(inst):
            self.cond_cache = inst
            return False

        if self.isFakeCond(inst):
            self.nopInst(self.cond_cache)
            self.cond_cache = inst
            return False

        if self.isConditionalJump(inst):
            self.cond_cache = None
            return False

        if self.isChangeFlow(inst) and not self.isUnConditionalJump(inst):
            self.nopInst(self.cond_cache)
            self.cond_cache = None
            self.mov_opt = None
            return False

        if self.isChangeZf(inst) and self.cond_cache:
            self.nopInst(self.cond_cache)
            self.cond_cache = None
            return False

        return False

    def optimize(self, inst):
        """
        Given an instruction, applies various optimization techniques to it, if possible.
        """
        numOperands = inst.getNumOperands()
        mn = inst.getMnemonicString()

        if numOperands == 2 \
            and inst.getOperandType(1) & OperandType.SCALAR \
            and (inst.getOperandType(0) & OperandType.DYNAMIC or inst.getOperandType(0) & OperandType.REGISTER):
                if mn == "MOV":
                    #print('SAVE: 0x{}: {}'.format(inst.getAddress(), inst))
                    self.mov_opt = inst
                    return

                if self.mov_opt == None:
                    #print('RET_1: 0x{}: {}'.format(addr, inst))
                    return

                mn_allowed = ['ADD', 'XOR', 'SUB']
                if not mn in mn_allowed:
                    return

                is_push = self.mov_opt.getMnemonicString() == 'PUSH'

                if not is_push and inst.getOpObjects(0)[0] != self.mov_opt.getOpObjects(0)[0]:
                    #print('RET_2: 0x{}: {}'.format(addr, inst))
                    self.mov_opt = None
                    return

                curr_val = inst.getOpObjects(1)[0].getValue()
                if is_push:
                    prev_val = self.mov_opt.getOpObjects(0)[0].getValue()
                else:
                    prev_val = self.mov_opt.getOpObjects(1)[0].getValue()

                result = None

                #print('CALC: 0x{}: {}'.format(inst.getAddress(), inst))

                target_reg = inst.getRegister(0)
                if target_reg:
                    res_len = int((target_reg.getBitLength() // 8) * 'FF', 16)
                else:
                    def_op = inst.getDefaultOperandRepresentation(0)
                    if def_op.startswith('byte ptr'):
                        res_len = 1
                    elif def_op.startswith('word ptr'):
                        res_len = 2
                    else:
                        res_len = 4

                if mn == "ADD":
                    result = (prev_val + curr_val) & res_len
                elif mn == "XOR":
                    result = (prev_val ^ curr_val) & res_len
                elif mn == "SUB":
                    result = (prev_val - curr_val) & res_len

                if result == None:
                    self.mov_opt = None
                    return

                prev_addr = self.mov_opt.getAddress()

                if is_push:
                    inst_asm = 'PUSH ' + hex(result).rstrip("L")
                    print('IS_PUSH: 0x{}: {}'.format(prev_addr, self.mov_opt))
                else:
                    inst_asm = str(self.mov_opt).split(',')[0] + ', ' + hex(result).rstrip("L")

                #print('Previously at: 0x{}: {}'.format(prev_addr, self.mov_opt))

                self.nopInst(inst)
                self.nopInst(self.mov_opt)

                self.asm.assemble(prev_addr, inst_asm)

                self.mov_opt = self.listing.getInstructionAt(prev_addr)

                return

        if numOperands == 1 and inst.getOperandType(0) & OperandType.SCALAR:
            if mn == "PUSH":
                #print('SAVE: 0x{}: {}'.format(addr, inst))
                self.mov_opt = inst
                return

    def clearBlock(self, address):
        """
        Given an address, clears the block at that address of any junk instructions.
        """
        block = self.dismBlock(address)
        if block == None:
            return

        for inst in block:
            min_addr = inst.getAddress()
            inst_len = inst.getLength()

            if not self.filter(inst):
                self.optimize(inst)
                self.addNewTarget(inst)

            self.dismCodeUnit(min_addr, inst_len - 1)

    def dismCodeUnit(self, address, sz):
        """
        Given an address and a size, disassembles the code unit at that address of the
        given size.
        """
        if self.isUndefined(address):
            max_address = address.add(sz)
            restrictedSet = AddressSet(address, max_address)
            self.disassembler.disassemble(address, restrictedSet)

    def deobfuscate(self):
        """
        Deobfuscates the GuLoader's code by clearing each block of junk instructions.
        """
        self.next_block.put(self.entry_point)
        while not self.next_block.empty():
            next_block = self.next_block.get()
            self.clearBlock(next_block)

if __name__ == "__main__":
    gu = GuDeobfuscator(currentLocation.getAddress()).deobfuscate()
