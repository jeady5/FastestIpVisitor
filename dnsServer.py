import dns.resolver
import requests
import time

server_list_url = 'https://gitee.com/jeadyx/global-dns-server/raw/master/server.json'
nameservers = requests.get(server_list_url).json()['data']

def getDNSInfos(domain:str, callback, stopEvet):
    resolver = dns.resolver.Resolver(configure=False)
    for server in nameservers:
        if stopEvet.isSet():
            break
        resolver.nameservers = [server]
        try:
            answers = resolver.resolve(domain, 'A', lifetime=1)
            for answer in answers:
                ip = str(answer)
                callback(ip)
                time.sleep(0.1)
        except Exception as e:
            pass
    callback("Done.")