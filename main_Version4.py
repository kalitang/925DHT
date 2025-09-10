import requests
import yaml
import random
from concurrent.futures import ThreadPoolExecutor

# 可补充更多免费clash订阅源
SUB_LINKS = [
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ClashPremium.yaml",
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/clash.yaml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml"
]

OUTPUT_FILE = "subscription.yaml"
FINAL_NODE_COUNT = 20

RULE_TEMPLATE = '''
port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info
external-controller: :9090
proxies: []
proxy-groups:
  - name: 🚀 节点选择
    type: select
    proxies: []
  - name: ♻️ 自动选择
    type: url-test
    proxies: []
    url: http://www.gstatic.com/generate_204
    interval: 300
  - name: 🎥 流媒体解锁
    type: select
    proxies:
      - 🚀 节点选择
      - DIRECT
  - name: 🍎 苹果服务
    type: select
    proxies:
      - DIRECT
      - 🚀 节点选择
  - name: 🛑 广告拦截
    type: select
    proxies:
      - REJECT
      - DIRECT
      - 🚀 节点选择
rules:
  - DOMAIN-SUFFIX,local,DIRECT
  - DOMAIN-KEYWORD,google,🚀 节点选择
  - DOMAIN-KEYWORD,facebook,🚀 节点选择
  - DOMAIN-KEYWORD,netflix,🎥 流媒体解锁
  - DOMAIN-KEYWORD,openai,🎥 流媒体解锁
  - DOMAIN-KEYWORD,telegram,🎥 流媒体解锁
  - DOMAIN-KEYWORD,youtube,🎥 流媒体解锁
  - DOMAIN-KEYWORD,twitter,🎥 流媒体解锁
  - DOMAIN-KEYWORD,instagram,🎥 流媒体解锁
  - DOMAIN-KEYWORD,github,🚀 节点选择
  - GEOIP,CN,DIRECT
  - MATCH,🚀 节点选择
'''

def fetch_yaml(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = yaml.safe_load(resp.text)
        if isinstance(data, dict) and 'proxies' in data:
            return data['proxies']
    except Exception as e:
        print(f"Failed fetch {url}: {e}")
    return []

def test_proxy(proxy):
    # 虚拟测速（如需真实测速可用 clash/api 或 ping 等方式拓展）
    delay = random.randint(30, 800)
    return delay

def main():
    all_nodes = []
    for link in SUB_LINKS:
        proxies = fetch_yaml(link)
        if proxies:
            all_nodes.extend(proxies)
        if len(all_nodes) >= 50:
            break

    # 去重
    seen = set()
    uniq_nodes = []
    for p in all_nodes:
        key = f"{p.get('name','')}-{p.get('server','')}-{p.get('port','')}"
        if key not in seen:
            uniq_nodes.append(p)
            seen.add(key)

    # 简单测速（按延迟升序取前20）
    with ThreadPoolExecutor(max_workers=10) as pool:
        delays = list(pool.map(test_proxy, uniq_nodes))
    nodes_with_delay = sorted(zip(uniq_nodes, delays), key=lambda x: x[1])
    fast_nodes = [n for n, d in nodes_with_delay[:FINAL_NODE_COUNT]]

    # 生成 yaml
    tpl = yaml.safe_load(RULE_TEMPLATE)
    tpl['proxies'] = fast_nodes
    proxy_names = [x['name'] for x in fast_nodes]
    for g in tpl['proxy-groups']:
        if g['name'] in ['🚀 节点选择', '♻️ 自动选择']:
            g['proxies'] = proxy_names
        elif g['name'] == '🎥 流媒体解锁':
            g['proxies'] = ['🚀 节点选择'] + proxy_names

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(tpl, f, allow_unicode=True)

if __name__ == '__main__':
    main()