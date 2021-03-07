import subprocess
from time import time,sleep
import os
from pathlib import Path
EXEC_FILE = Path(__file__).resolve().parents[0]/ "af.out"
print(EXEC_FILE)
import sys
import threading
import pexpect

class UAFShell:
    def __init__(self,exec):
        self.child = pexpect.spawn(str(exec))
    
    def cmd(self,args):
        self.child.send(args)
        self.child.expect("*.>")
        return self.child.after,self.child.before
    def read(self):
        self.child.expect("*.>")
        return self.child.after,self.child.before

a = UAFShell(EXEC_FILE)
#print(a.read())
while True:
    print(a.cmd(input()))


"""

class UAFShell:

    def __init__(self,exec):
        self.proc = subprocess.Popen(exec,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        self.start_date = time()
    
    def run(self):

        def write2process(p):
            try:
                while True:
                    d = p.stdout.read(1)
                    if not d or p.poll() is not None:
                        break
                    print(d.decode("utf-8"),end="")
            except EOFError:
                pass

        threading.Thread(target=write2process, args=(self.proc,)).start()
        

    def cmd(self,args):
        print(f"cmd {args}")
        self.proc.stdin.write(args.encode()+b'\n')
        self.proc.stdin.flush()
        print("titti")
    def close(self):
        self.proc.stdin.close()
        self.proc.terminate()
        self.proc.wait(timeout=0.2)


if __name__=="__main__":
    a = UAFShell(EXEC_FILE)
    a.run()
   
    while a.proc.poll() is not None:
        s = input()
        a.cmd(s)
"""