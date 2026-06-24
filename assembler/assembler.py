opcode = {'LI':0b000000, 
          'ADDI':0b000001,
          'LOOP':0b000010,
          'M_LD_W':0b000011,
          'M_MUL':0b000100,
          'ACT':0b000101,
          'STATUS':0b000110,
          'HALT':0b000111,
          'M_LD_A':0b001000,
          'M_ST':0b001001,}

registers = {'R0':0b00000,
             'R1':0b00001,
             'R2':0b00010,
             'R3':0b00011,
             'R4':0b00100,
             'R5':0b00101,
             'R6':0b00110,
             'R7':0b00111}
operand_count = {'LI':2,      #Rd, Imm
                 'ADDI':3,    #Rd, Rs1, Imm
                 'LOOP':2,    #Rs1, Imm/Label
                 'M_LD_W':1,  #Rs1
                 'M_MUL':2,   #Rd, Rs1
                 'ACT':2,     #Rs1, Immm
                 'STATUS':1,  #Rd
                 'HALT':0,
                 'M_LD_A':1,  #Rs1
                 'M_ST':2,}   #Rs1, Imm

def converter(inst):              
    if ';' in inst:               #remove commetns 
        inst = inst.split(';')[0]
    inst = inst.strip()           #remove whitespace

    if not inst:
        return None               #skipping empty line
       
    inst = inst.replace(',','')   #remove commas 
    token = inst.split() 
    token = [t.upper() for t in token]  #standardize case 
    return token

def assemble(token, line, labels): 
    if not token:
        return None
    op_mnemonic = token[0]
    if op_mnemonic not in opcode:
        print(f"Line {line}: Invalid opcode '{op_mnemonic}'")
        return None
    if (len(token) - 1) != operand_count[op_mnemonic]:
        print(f"Line {line}: Incorrect number of operands for '{op_mnemonic}'")
        return None
    op_val = opcode[op_mnemonic]
    rd = 0
    rs1 = 0
    imm = 0
    
    try:
        if op_mnemonic == 'LI':
            rd = registers[token[1]]
            imm = int(token[2],0) & 0xFFFF  #16-bit immediate
        elif op_mnemonic == 'ADDI':
            rd = registers[token[1]]
            rs1 = registers[token[2]]
            imm = int(token[3],0) & 0xFFFF  #16-bit immediate
        elif op_mnemonic == 'LOOP':
            rs1 = registers[token[1]]
            if token[2] in labels:
                imm = labels[token[2]] & 0xFFFF  #16-bit immediate
            else:
                imm = int(token[2],0) & 0xFFFF  #16-bit immediate
        elif op_mnemonic == 'M_LD_W':
            rs1 = registers[token[1]]
        elif op_mnemonic == 'M_MUL':
            rd = registers[token[1]]
            rs1 = registers[token[2]]
        elif op_mnemonic == 'ACT':
            rs1 = registers[token[1]]
            imm = int(token[2],0) & 0xFFFF  #16-bit immediate
        elif op_mnemonic == 'STATUS':
            rd = registers[token[1]]
        elif op_mnemonic == 'HALT':
            pass
        elif op_mnemonic == 'M_LD_A':
            rs1 = registers[token[1]]
        elif op_mnemonic == 'M_ST':
            rs1 = registers[token[1]]
            imm = int(token[2],0) & 0xFFFF  #16-bit immediate
    except KeyError as e:
        print(f"Line {line}: Invalid register '{e.args[0]}'")
        return None
    except ValueError as e:
        print(f"Line {line}: Invalid immediate value '{e.args[0]}'")
        return None
    
    machine_code = (op_val << 26) | (rd<<21) | (rs1<<16) | imm
    return f"{machine_code:08X}"

if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) != 3:
        print("Usage: python assembler.py <input_file.asm> <output_file.mem>")
        sys.exit(1)
    if not os.path.isfile(sys.argv[1]):
        print(f"Error: File '{sys.argv[1]}' not found.")
        sys.exit(1)
        
    labels = {}
    instructions = []
    current_address = 0

    with open(sys.argv[1], 'r') as fin:
        for line_num, line in enumerate(fin, 1):
            token = converter(line)
            if not token:
                continue
            if token[0].endswith(':'):
                label_name = token[0][:-1] # Remove colon
                labels[label_name] = current_address
                if len(token) > 1:
                    instructions.append((line_num, token[1:]))
                    current_address += 1
            else:
                instructions.append((line_num, token))
                current_address += 1  
                 
    with open(sys.argv[2], 'w') as fout:
        fout.write("@0000\n")  #BRAM initialization 
        for line_num, token in instructions:
            machine_code = assemble(token, line_num, labels)
            if machine_code:
                fout.write(machine_code + '\n')
    print(f"Compilation completed. Output written to '{sys.argv[2]}'")    