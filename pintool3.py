#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# prog_name= 'pintool3.py'
# prog_version = '3.0'
# prog_release = '20221203'
# prog_author = 'Tr4ccK'
# prog_author_mail = 'trackonyou@outlook.com'


import sys
import string as s
import subprocess
import argparse
import re


PINBASEPATH = '/home/track/CTF-Tools/pin-3.25-gcc-linux/'
PIN = PINBASEPATH + 'pin'
INSCOUNT32 = PINBASEPATH + 'source/tools/ManualExamples/obj-ia32/inscount0.so'
INSCOUNT64 = PINBASEPATH + 'source/tools/ManualExamples/obj-intel64/inscount0.so'


def start():
    parser = argparse.ArgumentParser(prog='pintool3.py')
    parser.add_argument('-e', dest='study', action='store_true', default=False, help='Study the password length, for example -e -l 40, with 40 characters')
    parser.add_argument('-l', dest='passlen', type=int, default=10, help='Length of password (Default: 10 )')
    parser.add_argument('-c', dest='charnum', type=str, help="Charset definition for brute force (1-Lowercase, 2-Uppecase, 3-Numbers, 4-Hexadecimal, 5-Punctuation, 6-All)")
    parser.add_argument('-b', dest='exchar', type=str, nargs=1, default='', help='Add characters for the charset, example -b _-')
    parser.add_argument('-a', dest='arch', type=str, nargs=1, default='64', help='Program architecture 32 or 64 bits, -a 32 or -a 64 (Default: 64)')
    parser.add_argument('-i', dest='initpass', type=str, nargs=1, default='', help='Inicial password characters, example -i CTF{')
    parser.add_argument('-s', dest='symbfill', type=str, nargs=1, default='_', help='Symbol for complete all password (Default: _ )')
    parser.add_argument('-d', dest='expression', type=str, nargs=1, default='!= 0', help="Difference between instructions that are successful or not (Default: != 0, example -d '== -12', -d '=> 900', -d '<= 17' or -d '!= 32')")
    parser.add_argument('-r', dest='reverse', action='store_true', default=False, help='Start in reverse order')
    parser.add_argument('filename', help='Program for playing with Pin Tool')

    if len(sys.argv) < 2:
        parser.print_help()
        print()
        print("Examples:")
        print("  ./pintool3.py -l 30 -c 1,2,3 -b _{} -s - baleful")
        print("  ./pintool3.py -l 37 -c 4 -i CTF{ -b }_ -s - -d '=> 651' reverse400")
        print("  ./pintool3.py -c 1,2,3 -b _ -s - -a 64 -l 28 wyvern")
        print("  ./pintool3.py -r -l 32 -c 1,2,3 -b _{$} -s - 01f47d58806a8264cd4b2b97b9dabb4a")
        print()
        sys.exit(1)

    args = parser.parse_args()
    return args

def getCharset(num):
    charset = {
        1: s.ascii_lowercase,
        2: s.ascii_uppercase,
        3: s.digits,
        4: s.hexdigits,
        5: s.punctuation,
        6: s.printable
    }

    char = ''
    if num == None:
        return charset[1]
    else:
        num = [int(i) for i in num.split(',')]
        assert all(1 <= i <= 6 for i in num), "Charset must be between 1 and 6"

    for i in num:
        char += charset[i]

    return char

def pin(passwd):
    try:
        command = f'echo {passwd} | {PIN} -t {INSCOUNT} -- ./{args.filename} ; cat inscount.out'
        output = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE)
    except:
        print(f"Unexpected error: {sys.exc_info()[0]}")
        raise

    output = re.findall(r"Count ([\w.-]+)", output.decode())
    return int(''.join(output))

def lengthdetect(passlen):
    inicialdifference = 0
    for i in range(1, passlen+1):
        password = "_" * i
        inscount = pin(password)

        if inicialdifference == 0:
            inicialdifference = inscount

        print(f"{password} = with {i} characters difference {inscount-inicialdifference} instructions")

def solve(initpass, passlen, symbfill, diffinst, charset, expression, reverse):
    initlen = len(initpass)
    for i in range(initlen, passlen):
        tempassword = initpass + symbfill * (passlen-i)
        inicialdifference = 0
        for char in charset:
            password = tempassword[:i] + char + tempassword[i+1:]
            if reverse:
                password = password[::-1]

            inscount = pin(password)
            if inicialdifference == 0:
                inicialdifference = inscount

            difference = inscount-inicialdifference
            print("%s = %d difference %d instructions" % (password, inscount, difference))
            sys.stdout.write("\033[F")
            cmpsym = expression.split()[0]
            match cmpsym:
                case '!=':
                    if difference != int(diffinst):
                        print("%s = %d difference %d instructions" %(password, inscount, difference))
                        initpass += char
                        break
                case '==':
                    if difference == int(diffinst):
                        print("%s = %d difference %d instructions" %(password, inscount, difference))
                        initpass += char
                        break

                case '<=':
                    if difference <= int(diffinst):
                        print("%s = %d difference %d instructions" %(password, inscount, difference))
                        initpass += char
                        break
                
                case '=>':
                    if difference >= int(diffinst):
                        print("%s = %d difference %d instructions" %(password, inscount, difference))
                        initpass += char
                        break

                case _:
                    print("Unknown value for -d option")
                    sys.exit()

            if char == charset[-1]:
                print("\n\nPassword not found, try to change charset...\n")
                sys.exit()

    return password.replace("\\", "", 1)

if __name__ == '__main__':
    args = start()
    initpass = ''.join(args.initpass)
    passlen = args.passlen
    symbfill = ''.join(args.symbfill)
    charset = symbfill + getCharset(args.charnum) + ''.join(args.exchar)
    arch = ''.join(args.arch)
    expression = ''.join(args.expression).strip()
    diffinst = expression.split()[1]
    study = args.study
    reverse = args.reverse

    assert len(initpass) < passlen, "Initial password must be less than password length"
    assert passlen <= 64, "Password length must be less or equal to 64"
    assert len(symbfill) == 1, "Symbol for complete all password must be only one character"
    assert arch in ['32','64'], "Architecture must be 32 or 64"
    INSCOUNT = eval('INSCOUNT' + arch)

    if study is True:
        lengthdetect(passlen)
        sys.exit()

    password = solve(initpass, passlen, symbfill, diffinst, charset, expression, reverse)
    print(f"\033[1;32m[+]\033[0m Password: {password}")