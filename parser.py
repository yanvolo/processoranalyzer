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
        regex = regex.replace("[:hex:]","0x[a-f0-9]+")
        regex = regex.replace("[:b16:]","[a-f0-9]+")
        regex = regex.replace("[:int:]","\s*\d+")
        regex = regex.replace("[:sym:]","\s*\S")
        regex = regex.replace("[:syms:]","\s*\S+")
        regex = regex.replace("[:eol:]","\s*\n")
        match = re.match(regex, self.remainingLineInput)
        if match:
            self.kvStore.update(match.groupdict())
            self.remainingLineInput = self.remainingLineInput[match.end():]
            if len(self.remainingLineInput) == 0:
                self.remainingLineInput = self.getLine()
        else:
            print("Mismatch occured at cycle %d following location:" % int(self.kvStore['cycle_count']))
            print(self.remainingLineInput[:300])
            print("Raising Error.")
            raise


    def matchAndConsumeMult(self, match_str, match_count):
        for n in range(0,match_count):
            parser.matchAndConsume(match_str.format(num=n))

    def matchAndConsumeInt(self, field_name):
        self.matchAndConsume("(?P<{name}>\s*\d+)".format(name=field_name))


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

slot_match = " +Slot\[{num}\]: V:[:sym:] Req:[:sym:] Wen:[:sym:] P:(?P<slot{num}_{slot_type}_P>\(\S,\S,\S\)) "
slot_match += "PRegs:Dst:\(Typ:(?P<slot{num}_{slot_type}_typ_code>\S) #:(?P<slot{num}_{slot_type}_typ_num>[:int:])\) "
slot_match += "Srcs:(?P<slot{num}_{slot_type}_srcs>\( *\d+, *\d+, *\d+\)) "
slot_match += "\[PC:(?P<slot{num}_{slot_type}_PC>[:hex:]) "
slot_match += "Inst:DASM\((?P<slot{num}_{slot_type}_DASM>[:b16:])\) "
slot_match += "UOPCode:(?P<slot{num}_{slot_type}_uopcode>[:int:])\] "
slot_match += "RobIdx:(?P<slot{num}_{slot_type}_robidx>[:int:]) "
slot_match += "BMsk:(?P<slot{num}_{slot_type}_BMsk>[:hex:]) "
slot_match += "Imm:(?P<slot{num}_{slot_type}_Imm>[:hex:])[:eol:]"

slot_iss_match = slot_match.format(slot_type="memIss", num="{num}")
slot_fp_match = slot_match.format(slot_type="fpIssue", num="{num}")
slot_int_match = slot_match.format(slot_type="int", num="{num}")

rob_match = " +ROB\[\s*{num}\]:(?P<rob{num}_statusCodes> *\S? *\S? *)\((?P<rob{num}_statusCodes2>\(\S\)\(\S\)\(\S\))"
rob_match += " +(?P<rob{num}_pc>[:hex:]) +\[DASM\((?P<rob{num}_dasm>[:b16:])\)\] (?P<rob{num}_ecode>[:sym:])"
rob_match += " \(d\:(?P<rob{num}_code>[:sym:]) (?P<rob{num}_pcode>p[:int:]), bm:(?P<rob{num}_bm>[:b16:])"
rob_match += " sdt: *(?P<rob{num}_sdt>[:int:])\)[:eol:]"

ftq_entry_match = "\s+\[Entry\:[:int:] Enq,Cmt,DeqPtr\:\((?P<ftq_{num}_code>(\w\s|\s)*(\w|\s))\) "
ftq_entry_match += "PC\:(?P<ftq_{num}_pc>[:hex:]) Hist\:(?P<ftq_{num}_hist>[:hex:]) "
ftq_entry_match += "CFI\:\(Exec,Mispred,Taken:\((?P<ftq_{num}_cfi_code>(\w\s|\s)*(\w|\s))\) Type:(?P<ftq_{num}_type>[:syms:]) "
ftq_entry_match += "\s*Idx:(?P<ftq_{num}_idx>[:int:])\) "
ftq_entry_match += "BIM:\(Idx:\s*(?P<ftq_{num}_bim_idx>[:int:]) Val:(?P<ftq_{num}_bim_val>[:hex:])\)\][:eol:]"

rega_match = "Register Number\s*{num} = (?P<register_a_{num}>[:b16:])[:eol:]"
regb_match = "Register Number\s*{num} = (?P<register_b_{num}>[:b16:])[:eol:]"

bim_bank_match = "\s+Bank\[ *{num}\]\: REN:(?P<bim{num}_ren>[:syms:]) WEN:(?P<bim{num}_wen>[:syms:]) "
bim_bank_match += "(WAddr:\([:int:]=[:hex:]\) Data:[:hex:] Msk:[:hex:] )?"
bim_bank_match += "UpdQ:\(Enq:(?P<bim{num}_enq>\(.*\)) (Deq:\(V:[:sym:] R:[:sym:]\))?S0_RMW:(?P<bim{num}_s0_rmw>\S)"
bim_bank_match += " S2_OUT:(?P<bim{num}_s2_out>[:hex:]) RMW_DATA:(?P<bim{num}_rmw_data>[:hex:]) "
bim_bank_match += "WrQ:\(EnqV:\s*(?P<bim{num}_wrq_enqv>[:int:]) DeqV:\s*(?P<bim{num}_wrq_deqv>[:int:])\)[:eol:]"

match_btb_write = "\s+Write \([:sym:]\): \(TAG\[{num}\]\[[:int:]\] \<\- [:hex:]\)\s+\(PC:[:hex:] TARG:[:hex:]\)[:eol:]"

cycle_count = 0
debug = True

while parser.hasInput():
    parser.kvStore.update({"Test Name":test_name})
    #Read Header
    parser.matchAndConsume("\-+ Cycle=(?P<cycle_count>[:int:]) \-+ Retired Instrs=(?P<retired_instrs>[:int:]) \-+[:eol:]")
    #Read Decode
    parser.matchAndConsume("Decode:[:eol:]")
    parser.matchAndConsume("\s+Slot:0 \(PC:(?P<decode_pc>[:hex:]) Valids:(?P<decode_valids>\S{2}) Inst:DASM\((?P<decode_inst_dasm>[:b16:])\)\)[:eol:]")
    #Read Rename
    parser.matchAndConsume("Rename:[:eol:]")
    parser.matchAndConsume("\s+Slot:0 \(PC:(?P<rename_pc>[:hex:]) Valid:(?P<rename_valid>[:sym:]) Inst:DASM\((?P<rename_inst_dasm>[:b16:])\)\)[:eol:]")
    #Decode Finished
    parser.matchAndConsume("Decode Finished:0x0[:eol:]")
    # Dispatch
    parser.matchAndConsume("Dispatch:[:eol:]")
    parser.matchAndConsume("\s+Slot:0 \(ISAREG: DST:(?P<dispatch_dst>[:int:]) SRCS:(?P<dispatch_srcs>([:int:],)*[:int:])\) \(PREG:(?P<dispatch_preg>\s*\((\S+,)*\S+\)(\s*\d+\[\S\]\(\S\)){4}\))[:eol:]")
    #ROB
    parser.matchAndConsume("ROB:[:eol:]")
    parser.matchAndConsume("\s+\(State\:(?P<ROB_state>[:syms:]) Rdy:(?P<ROB_rdy>[:sym:]) LAQFull:(?P<ROB_laqfull>[:sym:]) STQFull:(?P<ROB_stqfull>[:sym:]) Flush:(?P<ROB_flush>[:sym:]) BMskFull:(?P<ROB_bmskfull>[:sym:])\) BMsk:(?P<ROB_bmsk>[:hex:]) Mode:(?P<ROB_mode>[:sym:])[:eol:]")
    #Other
    parser.matchAndConsume("Other:[:eol:]")
    parser.matchAndConsume("\s+Expt:\(V:(?P<other_expt_v>[:sym:]) Cause:(?P<other_expt_cause>[:int:])\) Commit:(?P<other_commit>[:int:]) IFreeLst:(?P<other_ifreelst>[:hex:]) TotFree:(?P<other_totfree>[:int:]) IPregLst:(?P<other_ipreglst>[:hex:]) TotPreg:(?P<other_totpreg>[:int:])[:eol:]")
    parser.matchAndConsume("\s+FFreeList:(?P<other_ffreelist>[:hex:]) TotFree:(?P<other_totfreelst>[:int:]) FPrefLst:(?P<other_fpreflst>[:hex:]) TotPreg:(?P<other_totpreglst>[:int:])[:eol:]")
    #Branch Unit
    parser.matchAndConsume("Branch Unit:[:eol:]")
    parser.matchAndConsume("\s+V:(?P<branchUnit_v>\S) Mispred:(?P<branchUnit_mispred>\S) T/NT:(?P<branchUnit_tnt>\S) NPC:(?P<branchUnit_npc>\(V:\S PC:[:hex:]\))[:eol:]")
    parser.matchAndConsume("(\d [:hex:] \([:hex:]\) x[:int:] [:hex:][:eol:]|\d [:hex:] \([:hex:]\)[:eol:])?") #@TODO (high): What does this optional line represent?
    #Int Issue Slots
    parser.matchAndConsume("int issue slots:[:eol:]")

    parser.matchAndConsumeMult(slot_int_match,8)
    #Fetch Buffer
    parser.matchAndConsume("FetchBuffer:[:eol:]")
    parser.matchAndConsume("\s+Fetch3: Enq:\(V:(?P<fetchbuffer_3_enq_v>\S) Msk:(?P<fetchbuffer_3_enq_msk>[:hex:]) PC:(?P<fetchbuffer_3_enq_pc>[:hex:])\) Clear:(?P<fetchbuffer_3_clear>\S)[:eol:]")
    parser.matchAndConsume("\s+RAM: WPtr:(?P<fetchbuffer_3_ram_wptr>[:int:]) RPtr:(?P<fetchbuffer_3_ram_rptr>[:int:])[:eol:]")
    parser.matchAndConsume("\s+Fetch4: Deq:\(V:(?P<fetchbuffer_4_deq_v>\S) PC:(?P<fetchbuffer_4_deq_pc>[:hex:])\)[:eol:]")
    #Mem Issue Slots
    parser.matchAndConsume("mem issue slots:[:eol:]")
    parser.matchAndConsumeMult(slot_iss_match, 8)
    #fp issue slots
    parser.matchAndConsume("\s*fp issue slots:[:eol:]")
    parser.matchAndConsumeMult(slot_fp_match, 8)
    #BR-Unit
    parser.matchAndConsume("BR-UNIT:[:eol:]")
    parser.matchAndConsume("\s+PC:(?P<brUnit_pc>[:hex:]\+[:hex:]) Next:\(V:(?P<brUnit_next_v>\S) PC:(?P<brUnit_next_pc>[:hex:])\) BJAddr:(?P<brUnit_bjaddr>[:hex:])[:eol:]")
    #ROB
    parser.matchAndConsume("ROB:[:eol:]")
    parser.matchAndConsume("\s+Xcpt: V:(?P<rob_v>\S) Cause:(?P<rob_cause>[:hex:]) RobIdx:(?P<rob_idx>\s*\d+) BMsk:(?P<rob_bmsk>[:hex:]) BadVAddr:(?P<rob_badvaddr>[:hex:])[:eol:]")
    parser.matchAndConsumeMult(rob_match, 32)
    #FTQ
    parser.matchAndConsume("FTQ:[:eol:]")
    parser.matchAndConsume("\s+(?P<ftq_dequeue_status>No dequeue|(?P<ftq_dequeue>)\s+Dequeue: Ptr:[:int:] FPC:[:hex:] Hist:[:hex:] BIM:\(Idx:\([:int:]=[:b16:]\) V:[:sym:] Mispred:[:sym:] Taken:[:sym:] CfiIdx:[:int:] CntVal:[:int:] CfiType:[:syms:])[:eol:]")
    # parser.matchAndConsume("\s+(?P<ftq_dequeue>No dequeue|Dequeue: Ptr: (?P<ftq_dequeue_ptr_num>\s*\d+) FPC:(?P<ftq_dequeue_fpc>0x[0-9a-f]+) Hist:0x294 BIM:(Idx:(  24=018) V:- Mispred:- Taken:- CfiIdx:3 CntVal:2 CfiType:----)[:eol:]")
    parser.matchAndConsume("\s+Enq:\(V:(?P<ftq_enq_v>[:sym:]) Rdy:(?P<ftq_enq_rdy>[:sym:]) Idx:(?P<ftq_enq_idx>[:int:])\) Commit:\(V:(?P<ftq_commit_v>[:sym:]) Idx:(?P<ftq_commit_idx>[:int:])\) BRInfo:\(V&Mispred:[:sym:] Idx:[:int:]\) Enq,Cmt,DeqPtrs:(?P<ftq_brinfo_addr>\(([:int:])*([:int:])\))[:eol:]")
    parser.matchAndConsumeMult(ftq_entry_match, 16)
    parser.matchAndConsume("[:eol:]")
    #Registers
    parser.matchAndConsumeMult(rega_match, 48) #Group A Match
    parser.matchAndConsumeMult(regb_match, 52)  # Group B Match
    #BPD Pipeline
    parser.matchAndConsume("BPD Pipeline:[:eol:]")
    parser.matchAndConsume("\s+BTB: F0NPC:\(V:(?P<btb_f0npc_v>[:sym:]) PC:(?P<btb_f0npc_pc>[:hex:])\) F2RESP:\(V:(?P<btb_f2resp_v>[:sym:]) TRG:(?P<btb_f2resp_trg>[:hex:])\)[:eol:]")
    #BIM
    parser.matchAndConsume("BIM:[:eol:]")
    parser.matchAndConsume("\s+ReqPC:(?P<bim_reqpc>[:hex:]) \(LIdx:(?P<bim_lidx>[:int:]) BnkIdx:(?P<bim_bnkidx>[:int:]) Row:(?P<bim_row>[:int:])\) S2RespIdx:(?P<bim_s2respidx>[:int:])[:eol:]")
    parser.matchAndConsumeMult(bim_bank_match,2)
    #Fetch Monitor
    parser.matchAndConsume("FetchMonitor:[:eol:]")
    parser.matchAndConsume("\s+Fetch4:[:eol:]")
    parser.matchAndConsume("\s+UOP\[0\]: Fire:(?P<fetchmonitor_4_fire>[:sym:]) V:(?P<fetchmonitor_4_v>[:sym:]) PC:(?P<fetchmonitor_4_pc>[:hex:])[:eol:]")
    #BTB-SA
    parser.matchAndConsume("BTB-SA:[:eol:]")
    parser.matchAndConsumeMult(match_btb_write,2)
    parser.matchAndConsume("\s+Predicted \([:sym:]\): Hits:[:b16:] \(PC:[:hex:] \-\> TARG:[:hex:]\) CFI:[:syms:][:eol:]")
    parser.matchAndConsume("\s+BIM: Predicted \([:sym:]\): Idx:[:int:] Row:[:hex:][:eol:]")
    #Fetch Controller
    parser.matchAndConsume("Fetch Controller:[:eol:]")
    parser.matchAndConsume("\s+Fetch1:[:eol:]")
    parser.matchAndConsume("\s+BRUnit: V:(?P<fetchcontroller_1_v>[:sym:]) Tkn:(?P<fetchcontroller_1_tkn>[:sym:]) Mispred:(?P<fetchcontroller_1_mispred>[:sym:]) F0Redir:(?P<fetchcontroller_1_f0redir>\S) TakePc:(?P<fetchcontroller_1_takepc>.) RedirPc:(?P<fetchcontroller_1_redirpc>[:hex:])[:eol:]")
    parser.matchAndConsume("\s+Fetch2:[:eol:]")
    parser.matchAndConsume("\s+IMemResp: V:(?P<fetchcontroller_2_v>[:sym:]) Rdy:(?P<fetchcontroller_2_rdy>[:sym:]) PC:(?P<fetchcontroller_2_pc>[:hex:]) Msk:(?P<fetchcontroller_2_msk>[:hex:])[:eol:]")
    parser.matchAndConsume("\s+DASM\((?P<fetchcontroller_2_dasm1>[:b16:])\) DASM\((?P<fetchcontroller_2_dasm2>[:b16:])\) DASM\((?P<fetchcontroller_2_dasm3>[:b16:])\) DASM\((?P<fetchcontroller_2_dasm4>[:b16:])\)[:eol:]")
    parser.matchAndConsume("\s+IMemResp: BTB: Tkn:(?P<fetchcontroller_2_tkn>\S) Idx:(?P<fetchcontroller_2_idx>\d+) TRG:(?P<fetchcontroller_2_trg>[:hex:])[:eol:]")
    parser.matchAndConsume("\s+Fetch3:[:eol:]")
    parser.matchAndConsume("\s+FbEnq: V:(?P<fetchcontroller_3_v>\S) PC:(?P<fetchcontroller_3_pc>[:hex:]) Msk:(?P<fetchcontroller_3_msk>[:hex:])[:eol:]")
    #@TODO: (High) Parameterize all these fields properly
    #@TODO: (High) Test script on other debug logs.
    #@TODO: (High) Investigate Scala interface

    #@TODO: (Low) Add "Loading Bar" or some kind of status indicator to provide feedback to user as file is parsed

    #@TODO: (Low) Add code that converts values to right type to make it easier to manipulate down the line
    parser.commitLine()
    print("\rOn Cycle %d" %cycle_count),
    cycle_count = cycle_count + 1

if debug:
    print(parser.remainingLineInput)
    print(parser.peek_line())
    # print("////////////////////////")
    # print(parser.kvStore)


