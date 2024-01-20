import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import racentDNS
import dnsServer
import re
import threading
import inspect
import os, stat
from common import *
import time

class HandleState:
    Idle = 0 # 状态闲置
    Working = 1 # 正在获取

dnsHandlerList = [
    {
        "flag": "racentDNS", # 文件名
        "state": HandleState.Idle,
        "handler": racentDNS.getDNSInfos # 获取IP列表的方法，逐一回调
    },
    {
        "flag": "dnsServer",
        "state": HandleState.Idle,
        "handler": dnsServer.getDNSInfos
    },
]
ip_status = {}
ip_getter_stop_events = []
ping_threads = []
querying = False
domain_input = ''
title = 'Local Fastest Visitor'
def query_data(text_input):
    global querying
    if querying:
        for evt in ip_getter_stop_events:
            evt.set()
        return
    global domain_input
    domain_input = text_input
    if len(domain_input) == 0:
        messagebox.showinfo(title='Tip', message='Empty domain')
        return
    initParams()
    querying = True
    label_status['text'] = f"Working(2/{len(dnsHandlerList)})"
    query_button['text'] = "Done"
    root.title(f"{title} - {domain_input}")
    for dnsHandle in dnsHandlerList:
        evt = threading.Event()
        thr = threading.Thread(target=lambda: dnsHandle['handler'](domain_input, postIp, evt), daemon=True)
        thr.start()
        ip_getter_stop_events.append(evt)

def initParams():
    ip_getter_stop_events.clear()
    ping_threads.clear()
    ip_status.clear()
    for i in tree.get_children():
        tree.delete(i)
    for handler in dnsHandlerList:
        handler['state'] = HandleState.Working

lock = threading.Lock()
def postIp(data: str):
    print(time.ctime(), "hit ", data)
    lock.acquire()
    caller_flag = os.path.basename(inspect.stack()[1].filename).rstrip('.py').rstrip('.pyc')
    if re.match(r'^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$', data):
        ip = data
        if ip not in ip_status.keys():
            handleData({"ip": ip, "status": "querying", "hit": "1"})
            lastThread = threading.Thread(target=ping_local, args=(ip, handleData))
            lastThread.start()
            ping_threads.append(lastThread)
            ip_status[ip] = {"status": "querying", "hit": "1"}
        else:
            countHit = str(int(ip_status[ip]['hit'])+1)
            ip_status[ip] = {"status": "querying", "hit": countHit}
            handleData({"ip": ip, "hit": countHit})
    elif data.startswith("Done."):
        doneQuery(caller_flag)
    else:
        messagebox.showerror(title="Error", message=data)
    lock.release()

lockHandle = threading.Lock()
def handleData(data):
    lockHandle.acquire()
    if type(data) is dict:
        target = None
        for key in tree.get_children():
            ip = tree.item(key)['values'][0]
            if ip == data['ip']:
                target = key
                break
        if target is not None:
            if data.get('hit', None):
                tree.set(target, 'hit', data['hit'])
            elif data.get('status', None):
                tree.set(target, 'delay', data['status'])
        else:
            tree.insert("", tk.END, values=[data['ip'], "1", data['status']]) 
    lockHandle.release()

def doneQuery(flag):
    taskCompleted = 0
    global querying
    if querying:
        for handler in dnsHandlerList:
            if handler['flag'] == flag:
                handler['state'] = HandleState.Idle
            if handler['state'] == HandleState.Idle:
                taskCompleted += 1
    total = len(dnsHandlerList)
    label_status['text'] = f"Working({total-taskCompleted}/{total})"
    if taskCompleted == total:
        label_status['text'] = f"Waiting ping."
        while len(ping_threads):
            for thr in ping_threads:
                if not thr.is_alive():
                    ping_threads.remove(thr)
            time.sleep(1)
        querying = False
        root.title(title)
        infos = []
        count_valid = 0 # 可用的有几个
        count_nums = len(tree.get_children()) # 一共多少个ip
        count_all = 0 # 获取到了多少；一共击中了几个
        for child in tree.get_children():
            ip,num,status = tree.item(child)['values']
            count_all += int(num)
            if status.startswith("时间"):
                count_valid += 1
                delay = int(status.split('时间=')[1].rstrip("ms"))
                infos.append({
                    'ip': ip,
                    'status': delay
                })
            tree.delete(child)
        label_status['text'] = f"IP统计: 击中{count_all}个 合法{count_nums}个 可用{count_valid}个"
        query_button['text'] = "Go"
        infos = sorted(infos, key=lambda item: item['status'])
        for info in infos:
            ip = info['ip']
            tree.insert("", tk.END, values=(ip, ip_status[ip]['hit'],  f"{info['status']}ms"))
        if len(infos) == 0:
            messagebox.showinfo(title="Tip", message='No valid ip found.')
        else:
            messagebox.showinfo(title="Tip", message='Done.')

hostsDirOpened = False
def setToHosts(text: str):
    new_line = text.split(' ')
    if len(new_line)!=2:
        messagebox.showerror("Error", "error format")
        return
    domain = new_line[1]
    indicator = "## --- insert by fastdns --- \n"
    hostsPath = r'C:\Windows\System32\drivers\etc\hosts'
    os.chmod(hostsPath, stat.S_IWRITE)
    try:
        with open(hostsPath, 'r+',encoding= 'utf-8') as f:
            lines = f.readlines()
            for idx,line in enumerate(lines):
                res = re.match(fr"^\d.*? ({domain})([#\s\n]|$)", line)
                if res:
                    lines[idx] = f"# {line}"

            existIdx = -1
            if lines.count(indicator) >0:
                existIdx = lines.index(indicator)
                lines.insert(existIdx+1, f"{text}\n")
            else:
                lines.append(f"\n{indicator}")
                lines.append(text)
            f.seek(0)
            f.writelines(lines)
            messagebox.showinfo("Success", f"{text} has been wroted.")
    except PermissionError as err:
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showerror("写入hosts失败", f"解决方案：\n    1. 以管理员身份运行本程序.\n    2. 手动粘贴到hosts文件。\n\n{err}")
        global hostsDirOpened
        if not hostsDirOpened:
            hostsDirOpened = True
            os.system(f"explorer {os.path.dirname(hostsPath)}")
    os.chmod(hostsPath, stat.S_IREAD)

##### ui start #####
def tree_click_handler(event):   
    cItem = tree.item(tree.identify_row(event.y))['values']
    if len(cItem) > 0:
        ip = cItem[0]
        data = f"{ip} {domain_input}"
        setToHosts(data)

def center_window(root):
    size = (640, 480)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - size[0]) // 2
    y = (screen_height - size[1]) // 2
    root.geometry(f"{size[0]}x{size[1]}+{x}+{y}")

import webbrowser 
def open_url(event):
    webbrowser.open('https://gitee.com/jeadyx/local-fastest-visitor')

import pyuac
if __name__ == "__main__":
    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()
    else:
        root = tk.Tk()
        root.title(title)
        center_window(root)

        frame = tk.Frame(root)
        frame.pack(side=tk.TOP, fill=tk.X)

        label = tk.Label(frame, text='Domain:')
        label.pack(side=tk.LEFT)

        entry = tk.Entry(frame)
        entry.pack(side=tk.LEFT, padx=5)

        query_button = tk.Button(frame, text='Go', command=lambda: query_data(entry.get()))
        query_button.pack(side=tk.LEFT)

        label_status = tk.Label(frame, text="")
        label_status.pack(side=tk.RIGHT)

        columns = ("ip", "hit", "delay")
        tree = ttk.Treeview(root, columns=columns, show="headings")
        scrollbar = ttk.Scrollbar(root, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        for col in columns:
            tree.heading(col, text=col, anchor=tk.W)
        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        tree.bind('<ButtonRelease-1>', tree_click_handler)

        link = tk.Label(root, text='免责声明：本软件仅供学习使用, 相关ip数据来源于网络.', font=('Arial', 10), fg='#206020')
        link.pack(side=tk.BOTTOM)
        link.bind("<Button-1>", open_url)

        root.mainloop()
