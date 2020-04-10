import csv, sys, re


class Parser:
    def __init__(self, input_file_name, output_file_name, field_names):
        input_file_name = sys.argv[1]
        output_file_name = sys.argv[2]

        inputFile = open(input_file_name, "r")
        self.remainingInput = inputFile.read()
        inputFile.close()
        self.alignCycle()

        self.outputFile = open(output_file_name, "w")
        self.output = csv.DictWriter(self.outputFile,field_names)

        self.kvStore = {}

    def __del__(self):
        self.outputFile.close()

    def matchAndConsume(self, regex):
        match = re.match(regex, self.remainingInput)
        if match:
            self.kvStore.update(match.groupdict())
            self.remainingInput = self.remainingInput[match.end():]
        else:
            print("Mismatch occured at following location:")
            print(self.remainingInput[:300])
            print("Raising Error.")
            raise

    def commitLine(self):
        self.output.writerow(self.kvStore)
        self.kvStore = {}

    def alignCycle(self): #Aligns first cycle to begin parsing
        if self.hasInput():
            match = re.match("--- Cycle=",self.remainingInput)
            if not match:
                self.remainingInput = self.remainingInput[1:]
                self.alignCycle()

    def hasInput(self):
        return len(self.remainingInput)>0



#Start of actual Code
input_file_name = sys.argv[1]
output_file_name = sys.argv[2]
fieldNames = []
parser = Parser(input_file_name,output_file_name,fieldNames)

debug = True

while parser.hasInput():
    #Read Header
    parser.matchAndConsume("\-+ Cycle= +(?P<cycle_count>\d*) \-+ Retired Instrs= +(?P<retired_instrs>\d*) \-+\n")
    #Read Decode
    parser.matchAndConsume("Decode:\n +")
    parser.matchAndConsume("Slot:0 \(PC:(?P<decode_pc>0x[a-f0-9]+) Valids:-- Inst:DASM\((?P<decode_inst_dasm>\d+)\)\)\n")
    #Read Rename
    parser.matchAndConsume("Rename:\n +Slot:0 \(PC:(?P<rename_pc>0x[a-f0-9]+) Valid:- Inst:DASM\((?P<rename_inst_dasm>\d+)\)\)\n")
    #Decode Finished #Dispatch
    parser.matchAndConsume("Decode Finished:0x0\nDispatch:\n +Slot:0 \(ISAREG: DST: 2 SRCS: 2, 0, 2\) \(PREG: \(\#,Bsy,Typ\) 33\[-\]\(X\) +3\[R\]\(X\) +0\[R\]\(\-\) +0\[R\]\(\-\)\)\n")
    #ROB
    parser.matchAndConsume("ROB:\n")
    parser.matchAndConsume(" +\(State\:(?P<ROB_state>\S+) Rdy:\_ LAQFull:- STQFull:- Flush:- BMskFull:\-\) BMsk:0x0 Mode:U\n")
    #Other
    parser.matchAndConsume("Other:\n")
    parser.matchAndConsume(" +Expt:\(V:- Cause: +\d+\) Commit:0 IFreeLst:0xffffe00000080 TotFree:20 IPregLst:0x0000000000000 TotPreg: 0\n")
    parser.matchAndConsume(" +FFreeList:0xfffffffffffe TotFree:47 FPrefLst:0x000000000000 TotPreg: 0\n")
    #Branch Unit
    parser.matchAndConsume("Branch Unit:\n")
    parser.matchAndConsume(" +V:\- Mispred:\- T/NT:N NPC:\(V:V PC:0x000d0\)\n")
    #Int Issue Slots
    parser.matchAndConsume("int issue slots:\n")
    slot_match = " +Slot\[{slot_num}\]: V:\- Req:\- Wen:\- P:\(!,!,!\) "
    slot_match += "PRegs:Dst:\(Typ:(?P<slot{slot_num}_{slot_type}_typ_code>\S) #: *(?P<slot{slot_num}_{slot_type}_typ_num>\d+)\) "
    slot_match += "Srcs:(?P<slot{slot_num}_{slot_type}_srcs>\( *\d+, *\d+, *\d+\)) \[PC:(?P<slot{slot_num}_{slot_type}_PC>0x[a-f0-9]+) Inst:DASM\((?P<slot{slot_num}_{slot_type}_DASM>[a-f0-9]+)\) UOPCode: *(?P<slot{slot_num}_{slot_type}_uopcode>\d+)\] "
    slot_match += "RobIdx: *(?P<slot{slot_num}_{slot_type}_robidx>\d+) BMsk:(?P<slot{slot_num}_{slot_type}_BMsk>0x[a-f0-9]+) Imm:(?P<slot{slot_num}_{slot_type}_Imm>0x[a-f0-9]+)\n"
    for n in range(0,8):
        parser.matchAndConsume(slot_match.format(slot_num=n,slot_type="int"))
    #Fetch Buffer
    parser.matchAndConsume("FetchBuffer:\n")
    parser.matchAndConsume(" +Fetch3: Enq:\(V:\- Msk:0x5 PC:0x00800000e0\) Clear:\-\n")
    parser.matchAndConsume(" +RAM: WPtr:  1 RPtr:  1\n")
    parser.matchAndConsume(" +Fetch4: Deq:\(V:- PC:0x00800000c8\)\n")
    #Mem Issue Slots
    parser.matchAndConsume("mem issue slots:\n")
    for n in range(0,8):
        parser.matchAndConsume(slot_match.format(slot_num=n,slot_type="memIss"))


    # slot_match = " +Slot\[{slot_num}\]: V:\- Req:\- Wen:\- P:\(!,!,!\) "
    # slot_match += "PRegs:Dst:\(Typ:(?P<slot{slot_num}_int_typ_code>\S) #: *(?P<slot{slot_num}_int_typ_num>\d+)\) "
    # slot_match += "Srcs:(?P<slot{slot_num}_int_srcs>\( *\d+, *\d+, *\d+\)) \[PC:(?P<slot{slot_num}_int_PC>0x[a-f0-9]+) Inst:DASM\((?P<slot{slot_num}_int_DASM>[a-f0-9]+)\) UOPCode: *(?P<slot{slot_num}_int_uopcode>\d+)\] "
    # slot_match += "RobIdx: *(?P<slot{slot_num}_int_robidx>\d+) BMsk:(?P<slot{slot_num}_int_BMsk>0x[a-f0-9]+) Imm:(?P<slot{slot_num}_int_Imm>0x[a-f0-9]+)\n"
    # parser.matchAndConsume(slot_match.format(slot_num=6))

    if debug:
        print(parser.remainingInput[:300])
        # print("////////////////////////")
        # print(parser.kvStore)
    #@DEBUG: Remove when doing more than one cycle
    break

#Keep Reading File
reading_unfinished = True
# while reading_unfinished:
#     line = input.readline()
#     if("" == line):
#         reading_unfinished = False
#     else:
#         if(line[0] != '-'):
#             raise
#         pass




