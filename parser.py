import csv, sys, re


class Parser:
    def __init__(self, input_file_name, output_file_name):
        input_file_name = sys.argv[1]
        output_file_name = sys.argv[2]

        self.inputFile = open(input_file_name, "r")

        self.remainingLineInput = self.getLine()
        self.alignCycle()

        self.outputFile = open(output_file_name, "w")
        self.output = None

        self.kvStore = {}

    def __del__(self):
        self.outputFile.close()
        self.inputFile.close()

    def getLine(self):
        return self.inputFile.readline()

    def matchAndConsume(self, regex):
        match = re.match(regex, self.remainingLineInput)
        if match:
            self.kvStore.update(match.groupdict())
            self.remainingLineInput = self.remainingLineInput[match.end():]
            if len(self.remainingLineInput) == 0:
                self.remainingLineInput = self.getLine()
        else:
            print("Mismatch occured at following location:")
            print(self.remainingLineInput[:300])
            print("Raising Error.")
            raise


    def matchAndConsumeMult(self, match_str, match_count):
        for n in range(0,match_count):
            parser.matchAndConsume(match_str.format(num=n))

    def commitLine(self):
        if self.output == None:
            self.output = csv.DictWriter(self.outputFile,self.kvStore.keys())
            self.output.writeheader()
        self.output.writerow(self.kvStore)
        self.kvStore = {}

    def alignCycle(self): #Aligns first cycle to begin parsing
        match = re.match("--- Cycle=", self.remainingLineInput)
        while not match and self.hasInput():
            self.remainingLineInput = self.remainingLineInput[1:]
            if len(self.remainingLineInput) == 0:
                self.remainingLineInput = self.getLine()
            match = re.match("--- Cycle=", self.remainingLineInput)

    def hasInput(self):
        return len(self.remainingLineInput) > 0

    def peek_line(self):
        pos = self.inputFile.tell()
        line = self.inputFile.readline()
        self.inputFile.seek(pos)
        return line



#Start of actual Code
input_file_name = sys.argv[1]
output_file_name = sys.argv[2]
test_name = sys.argv[3]

fieldNames = []
parser = Parser(input_file_name,output_file_name)

slot_match = " +Slot\[{num}\]: V:\- Req:\- Wen:\- P:(?P<slot{num}_{slot_type}_P>\(\S,\S,\S\)) "
slot_match += "PRegs:Dst:\(Typ:(?P<slot{num}_{slot_type}_typ_code>\S) #:"
slot_match += " *(?P<slot{num}_{slot_type}_typ_num>\d+)\) "
slot_match += "Srcs:(?P<slot{num}_{slot_type}_srcs>\( *\d+, *\d+, *\d+\)) "
slot_match += "\[PC:(?P<slot{num}_{slot_type}_PC>0x[a-f0-9]+) "
slot_match += "Inst:DASM\((?P<slot{num}_{slot_type}_DASM>[a-f0-9]+)\) "
slot_match += "UOPCode: *(?P<slot{num}_{slot_type}_uopcode>\d+)\] "
slot_match += "RobIdx: *(?P<slot{num}_{slot_type}_robidx>\d+) "
slot_match += "BMsk:(?P<slot{num}_{slot_type}_BMsk>0x[a-f0-9]+) "
slot_match += "Imm:(?P<slot{num}_{slot_type}_Imm>0x[a-f0-9]+)\n"

slot_iss_match = slot_match.format(slot_type="memIss", num="{num}")
slot_fp_match = slot_match.format(slot_type="fpIssue", num="{num}")
slot_int_match = slot_match.format(slot_type="int", num="{num}")

rob_match = " +ROB\[ *{num}\]:(?P<rob{num}_statusCodes> *\S? *\S? *)\(\(\-\)\(\-\)\(\-\)"
rob_match += " +(?P<rob{num}_pc>0x[a-f0-9]+) +\[DASM\((?P<rob{num}_dasm>\d+)\)\] \-"
rob_match += " \(d\:(?P<rob{num}_code>\S) (?P<rob{num}_pcode>p *\d+), bm:(?P<rob{num}_bm>\d+)"
rob_match += " sdt: *(?P<rob{num}_sdt>\d+)\) *\n"

ftq_entry_match = "\s+\[Entry\:\s*{num} (?P<ftq_{num}_inst>(\S+\,)*\S+)\:\((?P<ftq_{num}_code>(\w\s|\s)*(\w|\s))\) "
ftq_entry_match += "PC\:(?P<ftq_{num}_pc>0x[0-9a-f]+) Hist\:(?P<ftq_{num}_hist>0x[0-9a-f]+) "
ftq_entry_match += "CFI\:\((?P<ftq_{num}_cfi>(\S+\,)*\S+):\((?P<ftq_{num}_cfi_code>(\w\s|\s)*(\w|\s))\) Type:(?P<ftq_{num}_type>\-+) "
ftq_entry_match += "Idx:(?P<ftq_{num}_idx>\d+)\) "
ftq_entry_match += "BIM:\(Idx:\s*(?P<ftq_{num}_bim_idx>\d+) Val:(?P<ftq_{num}_bim_val>0x[0-9a-f]+)\)\]\s*\n"

rega_match = "Register Number\s*{num} = (?P<register_a_{num}>[a-f0-9]*)\s*\n"
regb_match = "Register Number\s*{num} = (?P<register_b_{num}>[a-f0-9]*)\s*\n"

bim_bank_match = "\s+Bank\[ *{num}\]\: REN:(?P<bim{num}_ren>\S+) WEN:(?P<bim{num}_wen>\S+) "
bim_bank_match += "UpdQ:\(Enq:(?P<bim{num}_enq>\(.*\)) S0_RMW:(?P<bim{num}_s0_rmw>\S)"
bim_bank_match += " S2_OUT:(?P<bim{num}_s2_out>0x[a-f0-9]+) RMW_DATA:(?P<bim{num}_rmw_data>0x[a-f0-9]+) "
bim_bank_match += "WrQ:\(EnqV:\s*(?P<bim{num}_wrq_enqv>\d+) DeqV:\s*(?P<bim{num}_wrq_deqv>\d+)\)\s*\n"

match_btb_write = "\s+Write \(\-\): \(TAG\[{num}\]\[\s*\d+\] \<\- 0x[a-f0-9]+\)\s+\(PC:0x[a-f0-9]+ TARG:0x[a-f0-9]+\)\n"


debug = True

while parser.hasInput():
    parser.kvStore.update({"Test Name":test_name})
    #Read Header
    parser.matchAndConsume("\-+ Cycle= +(?P<cycle_count>\d*) \-+ Retired Instrs= +(?P<retired_instrs>\d*) \-+\n")
    #Read Decode
    parser.matchAndConsume("Decode:\n")
    parser.matchAndConsume("\s+Slot:0 \(PC:(?P<decode_pc>0x[a-f0-9]+) Valids:(?P<decode_valids>\S{2}) Inst:DASM\((?P<decode_inst_dasm>\d+)\)\)\n")
    #Read Rename
    parser.matchAndConsume("Rename:\n")
    parser.matchAndConsume("\s+Slot:0 \(PC:(?P<rename_pc>0x[a-f0-9]+) Valid:(?P<rename_valid>\S) Inst:DASM\((?P<rename_inst_dasm>\d+)\)\)\n")
    #Decode Finished
    parser.matchAndConsume("Decode Finished:0x0\n")
    # Dispatch
    parser.matchAndConsume("Dispatch:\n")
    parser.matchAndConsume("\s+Slot:0 \(ISAREG: DST:(?P<dispatch_dst>\s*\d+) SRCS:(?P<dispatch_srcs>(\s*\d+,)*\s*\d+)\) \(PREG:(?P<dispatch_preg>\s*\((\S+,)*\S+\)(\s*\d+\[\S\]\(\S\)){4}\))\n")
    #ROB
    parser.matchAndConsume("ROB:\n")
    parser.matchAndConsume("\s+\(State\:(?P<ROB_state>\S+) Rdy:(?P<ROB_rdy>\S) LAQFull:(?P<ROB_laqfull>\S) STQFull:(?P<ROB_stqfull>\S) Flush:(?P<ROB_flush>\S) BMskFull:(?P<ROB_bmskfull>\S)\) BMsk:(?P<ROB_bmsk>0x[0-9a-f]) Mode:(?P<ROB_mode>\S)\n")
    #Other
    parser.matchAndConsume("Other:\n")
    parser.matchAndConsume("\s+Expt:\(V:(?P<other_expt_v>\S) Cause:(?P<other_expt_cause>\s+\d+)\) Commit:(?P<other_commit>\s*\d+) IFreeLst:(?P<other_ifreelst>0x[a-f0-9]+) TotFree:(?P<other_totfree>\s*\d+) IPregLst:(?P<other_ipreglst>0x[a-f0-9]+) TotPreg:(?P<other_totpreg>\s*\d+)\n")
    parser.matchAndConsume("\s+FFreeList:(?P<other_ffreelist>0x[a-f0-9]+) TotFree:(?P<other_totfreelst>\s*\d+) FPrefLst:(?P<other_fpreflst>0x[a-f0-9]+) TotPreg:(?P<other_totpreglst>\s*\d+)\n")
    #Branch Unit
    parser.matchAndConsume("Branch Unit:\n")
    parser.matchAndConsume("\s+V:(?P<branchUnit_v>\S) Mispred:(?P<branchUnit_mispred>\S) T/NT:(?P<branchUnit_tnt>\S) NPC:(?P<branchUnit_npc>\(V:\S PC:0x[a-f0-9]+\))\n")
    #Int Issue Slots
    parser.matchAndConsume("int issue slots:\n")
    parser.matchAndConsumeMult(slot_int_match,8)
    #Fetch Buffer
    parser.matchAndConsume("FetchBuffer:\n")
    parser.matchAndConsume("\s+Fetch3: Enq:\(V:(?P<fetchbuffer_3_enq_v>\S) Msk:(?P<fetchbuffer_3_enq_msk>0x[a-f0-9]+) PC:(?P<fetchbuffer_3_enq_pc>0x[a-f0-9]+)\) Clear:(?P<fetchbuffer_3_clear>\S)\n")
    parser.matchAndConsume("\s+RAM: WPtr:  1 RPtr:  1\n")
    parser.matchAndConsume("\s+Fetch4: Deq:\(V:(?P<fetchbuffer_4_deq_v>\S) PC:(?P<fetchbuffer_4_deq_pc>0x[a-f0-9]+)\)\n")
    #Mem Issue Slots
    parser.matchAndConsume("mem issue slots:\n")
    parser.matchAndConsumeMult(slot_iss_match, 8)
    #fp issue slots
    parser.matchAndConsume("\s*fp issue slots:\n")
    parser.matchAndConsumeMult(slot_fp_match, 8)
    #BR-Unit
    parser.matchAndConsume("BR-UNIT:\n")
    parser.matchAndConsume("\s+PC:(?P<brUnit_pc>0x[a-f0-9]+\+0x[a-f0-9]+) Next:\(V:(?P<brUnit_next_v>\S) PC:(?P<brUnit_next_pc>0x[a-f0-9]+)\) BJAddr:(?P<brUnit_bjaddr>0x[a-f0-9]+)\n")
    #ROB
    parser.matchAndConsume("ROB:\n")
    parser.matchAndConsume("\s+Xcpt: V:(?P<rob_v>\S) Cause:(?P<rob_cause>0x[a-f0-9]+) RobIdx:(?P<rob_idx>\s*\d+) BMsk:(?P<rob_bmsk>0x[a-f0-9]+) BadVAddr:(?P<rob_badvaddr>0x[a-f0-9]+)\n")
    parser.matchAndConsumeMult(rob_match, 32)
    #FTQ
    parser.matchAndConsume("FTQ:\n")
    parser.matchAndConsume("\s+No dequeue\n")
    parser.matchAndConsume("\s+Enq:\(V:(?P<ftq_enq_v>\S) Rdy:(?P<ftq_enq_rdy>\S) Idx:(?P<ftq_enq_idx>\s*\d+)\) Commit:\(V:(?P<ftq_commit_v>\S) Idx:(?P<ftq_commit_idx>\s*\d+)\) BRInfo:\(V&Mispred:- Idx:    0\) Enq,Cmt,DeqPtrs:\( 8  7  7\)\n")
    parser.matchAndConsumeMult(ftq_entry_match, 16)
    parser.matchAndConsume(" *\n")
    #Registers
    parser.matchAndConsumeMult(rega_match, 48) #Group A Match
    parser.matchAndConsumeMult(regb_match, 52)  # Group B Match
    #BPD Pipeline
    parser.matchAndConsume("BPD Pipeline:\n")
    parser.matchAndConsume("\s+BTB: F0NPC:\(V:(?P<btb_f0npc_v>\S) PC:(?P<btb_f0npc_pc>0x[a-f0-9]+)\) F2RESP:\(V:(?P<btb_f2resp_v>\S) TRG:(?P<btb_f2resp_trg>0x[a-f0-9]+)\)\n")
    #BIM
    parser.matchAndConsume("BIM:\n")
    parser.matchAndConsume("\s+ReqPC:(?P<bim_reqpc>0x[a-f0-9]+) \(LIdx:\s*(?P<bim_lidx>\d+) BnkIdx:\s*(?P<bim_bnkidx>\d+) Row:\s*(?P<bim_row>\d+)\) S2RespIdx:\s*(?P<bim_s2respidx>\d+)\n")
    parser.matchAndConsumeMult(bim_bank_match,2)
    #Fetch Monitor
    parser.matchAndConsume("FetchMonitor:\n")
    parser.matchAndConsume("\s+Fetch4:\n")
    parser.matchAndConsume("\s+UOP\[0\]: Fire:- V:- PC:0x00800000c8\n")
    #BTB-SA
    parser.matchAndConsume("BTB-SA:\n")
    parser.matchAndConsumeMult(match_btb_write,2)
    parser.matchAndConsume("\s+Predicted \(\-\): Hits:[a-f0-9]+ \(PC:0x[a-f0-9]+ \-\> TARG:0x[0-9a-f]+\) CFI:\-+\n")
    parser.matchAndConsume("\s+BIM: Predicted \(V\): Idx: \d+ Row:0x[a-f0-9]+\n")
    #Fetch Controller
    parser.matchAndConsume("Fetch Controller:\n")
    parser.matchAndConsume("\s+Fetch1:\n")
    parser.matchAndConsume("\s+BRUnit: V:(?P<fetchcontroller_1_v>\S) Tkn:(?P<fetchcontroller_1_tkn>\S) Mispred:(?P<fetchcontroller_1_mispred>\S) F0Redir:(?P<fetchcontroller_1_f0redir>\S) TakePc:(?P<fetchcontroller_1_takepc>.) RedirPc:(?P<fetchcontroller_1_redirpc>0x[a-f0-9]+)\n")
    parser.matchAndConsume("\s+Fetch2:\n")
    parser.matchAndConsume("\s+IMemResp: V:(?P<fetchcontroller_2_v>\S) Rdy:(?P<fetchcontroller_2_rdy>\S) PC:(?P<fetchcontroller_2_pc>0x[a-f0-9]+) Msk:(?P<fetchcontroller_2_msk>0x[a-f0-9]+)\n")
    parser.matchAndConsume("\s+DASM\(0000\) DASM\(0000\) DASM\(0000\) DASM\(0000\)\s*\n")
    parser.matchAndConsume("\s+IMemResp: BTB: Tkn:- Idx:0 TRG:0x00000\n")
    parser.matchAndConsume("\s+Fetch3:\n")
    parser.matchAndConsume("\s+FbEnq: V:- PC:0x00800000e0 Msk:0x5\s*\n")
    #@TODO: (High) Parameterize all these fields properly and test on complete sample
    #@TODO: (High) Test script on other debug logs.


    #@TODO: (Low) Add code that converts values to right type to make it easier to manipulate down the line
    parser.commitLine()

if debug:
    print(parser.remainingLineInput)
    print(parser.peek_line())
    # print("////////////////////////")
    # print(parser.kvStore)


