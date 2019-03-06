import os
import client
import threading

class window():
    def __init__(self):
        self.waiting()

    def waiting(self):
        while (True):
            print("\nLFTP is open now.")
            print("---------------")
            print("lsend [server ip] [local file path] -- send a file to server")
            print("lget [server ip] [server file path] -- get a file from server")
            print("exit                                -- exit LFTP")
            print("---------------")
            s = str(input(r">>> LFTP: "))
            if (s == "exit"):
                break
            s = s.split(" ", 2)

            # format error
            if len(s) != 3:
                self.inputerror()
                self.waiting()
                return
            
            # command error
            elif s[0] != "lsend" and s[0] != "lget":
                self.cmderror(s[0])
                self.waiting()
                return
            
            # ip address error
            elif s[1] != "134.175.103.254":
                self.svrerror(s[1])
                self.waiting()
                return

            # filename error
            else:
                if s[0] == "lsend":
                    if not os.path.isfile(s[2]):
                        self.fileerror(s[2])
                        self.waiting()
                        return
                

            #execute
            #例：lsend 172.18.34.162 D:\lena.jpg
            #    lget 134.175.103.254 D:\lena.jpg
            try:
                newClient = client.client(s[0], s[1], s[2])
                newClient.run()
            except SyntaxError as e:
                print(e)
    
    def cmderror(self, s):
        print("Command " + s + " is invalid, please check your input.")

    def svrerror(self, s):
        print("IP address " + s + " is invalid, please check your input.")
    
    def fileerror(self, s):
        print("There is no file " + s + " in local system.")
    
    def fileerror2(self, s):
        print("There is no file " + s + " in server system.")

    def inputerror(self):
        print("Please use the format to input.")

test = window()