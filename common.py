
import subprocess

def ping_local(ip, callback):
    try:
        result = subprocess.getoutput(f"ping -n 3 -w 500 {ip}")
        line = result.split('\n')[3]
        info = line.split(' ')
        delay = line if len(info)<5 else info[4]
        pingResult = delay
    except Exception as e:
        pingResult = str(e)
    if callback is not None:
        callback({
            'ip': ip,
            'status': pingResult
        })


# import ctypes
# import sys

# def is_admin():
#     if ctypes.windll.shell32.IsUserAnAdmin() == 0:
#         return True
#     else:
#         return False
 
# def run_as_admin():
#     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

# def checkAdmin():
#     if not is_admin():
#         run_as_admin()
#     else:
#         admin_operation()

# def admin_operation(event):
#     with open(r"C:\test.txt", 'r+', encoding='utf16') as f:
#         f.write("hello admin pri")

#     with open(r"C:\Windows\system32\test.txt", 'w') as f:
#         f.write("hello admin pri")