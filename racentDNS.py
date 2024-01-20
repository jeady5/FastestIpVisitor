import requests
import time
import random

nodes_url = "http://face.racent.com/tool/enable_dns_nodes"
query_url = "http://face.racent.com/tool/query_my_dns?name={0}&dns_type=A&node={1}"
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def getDNSInfos(domain:str, callback, stopEvet):
    try:
        res = requests.get(nodes_url, headers=header, timeout=2)
    except Exception as e:
        callback(f'Done.Error: {e}')
        return
    node_json = res.json()
    if node_json['code'] == 0:
        nodes = node_json['data']['list']
        for node in nodes:
            if stopEvet.isSet():
                break
            node_name = node['name']
            url_detail = query_url.format(domain, node_name)
            try:
                res_get_ip = requests.get(url_detail, headers=header, timeout=2)
            except Exception as e:
                continue
            if res_get_ip.status_code == 200:
                ip_info_json = res_get_ip.json()
                if ip_info_json['code'] == 0:
                    ip_list = ip_info_json['data']['list']
                    for ipInfo in ip_list:
                        if stopEvet.isSet():
                            break
                        ip = ipInfo['value']
                        callback(ip)
            time.sleep(random.random())
        callback('Done.')
    else:
        callback(f"Done.Errcode: {node_json['code']}")