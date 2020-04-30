# %%
import re
import os
import requests
import logging
import sys
import time
import warnings
import random
import simplejson as json
from simplejson.decoder import JSONDecodeError
import requests
from requests.exceptions import RequestException
# %%
warnings.filterwarnings('ignore') #ignore std warning，don't mind

HEADER = {
    "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
    "cache-control": "max-age=0",
    "content-type": "application/x-www-form-urlencoded",
    "dnt": "1",
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}

PROXY = {
    "http": "http://127.0.0.1:1080",
    "https": "http://127.0.0.1:1080"
}

RETRY_NUM = 5

try:
    import brotli
    HEADER["accept-encoding"] = "gzip, deflate, br"
except ImportError as e:
    HEADER["accept-encoding"] = "gzip, deflate"

PATH = os.path.abspath(os.path.dirname(__file__))

logging.basicConfig(
    filename=os.path.join(PATH, 'checkin.log'),
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

if sys.version_info.major == 2:
    logging.getLogger("requests").setLevel(logging.WARNING)
# %%
def get_randint(min_num, max_num):
    if min_num > max_num:
        raise ValueError("Illegal arguments...")
    return random.randint(min_num, max_num)

def config_load(filename):
    if not os.path.exists(filename) or os.path.isdir(filename):
        return

    config = open(filename, 'r').read()
    return json.loads(config)

def extract_domain(url):
    if not url:
        return ""

    start = url.find("//")
    if start == -1:
        start = -2

    end = url.find("/", start + 2)
    if end == -1:
        end = len(url) - 1

    return url[start + 2:end]

# def login(url, params, cookies, headers, retry, proxy=False):
#     try:
#         if proxy:
#             response = requests.post(
#                 url, data=params, cookies = cookies, headers=headers, allow_redirects=True, proxies=PROXY, verify=False)
#         else:
#             response = requests.post(
#                 url, data=params, cookies = cookies, headers=headers, allow_redirects=True)

#         if response.status_code == 200:
#             return {str(key).lower(): value for key, value in response.headers.items()}
 
#     except RequestException as e:
#         logging.error(str(e))
#         retry -= 1

#         if retry > 0:
#             time.sleep(get_randint(30 * 60, 90 * 60))
#             login(url, params, headers, retry, proxy)

#         logging.error(u"登录失败 URL: {}".format(extract_domain(url)))
#         return None

def checkin(url, headers, form_data, retry, proxy=False):
    try:
        if proxy:
            response = requests.post(url, headers=headers, proxies=PROXY, verify=False)
        else:
            response = requests.post(url, headers=headers, data=form_data)
        print("+++++++++++++++++++++++++++")
        print(response.text)
        if response.status_code == 200:
            if response.text.find("已经签到") != -1:
                logging.info(u"已经签到 URL: {}".format(extract_domain(url)))
            else:
                logging.info(u"签到成功 URL: {}".format(extract_domain(url)))

            return 

    except RequestException as e:
        logging.error(str(e))
        retry -= 1

        if retry > 0:
            time.sleep(get_randint(30, 60 * 60))
            checkin(url, headers, retry, proxy)

        logging.error(u"签到失败 URL: {}".format(extract_domain(url)))

# def logout(url, headers):
#     try:
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             return 0
#         else:
#             logging.info(u"退出失败 URL: {}".format(extract_domain(url)))
#             return -3
#     except RequestException:
#         return -3

# def get_cookie(headers):
#     regex = "(__cfduid|uid|email|key|ip|expire_in)=(.+?);"
#     if "set-cookie" not in headers:
#         return ''

#     content = re.findall(regex, headers["set-cookie"])
#     cookie = ';'.join(['='.join(x) for x in content]).strip()

#     return cookie      

def flow(domain, params, headers, proxy=False):
    domain = domain.strip()# remvoe space in start and tail
    regex = "(?i)^(https?:\\/\\/)?(www.)?([^\\/]+\\.[^.]*$)"
    flag = re.search(regex, domain)

    if not flag:
        return False

    cookie = params["cookies"]
    headers["cookie"] = cookie
    form_data = params["form_data"]
    headers["origin"] = domain
    headers["referer"] = domain+"/plugin.php?id=dsu_paulsign:sign"
    checkin_url = headers["referer"]+"&operation=qiandao&infloat=1&inajax=1"
    checkin(checkin_url, headers, form_data, RETRY_NUM, proxy)

def wrapper(args):
    flow(args["domain"], args["param"], HEADER, args["proxy"])
# %%
config = config_load('./config.json')
if config is None or "domains" not in config or len(config["domains"]) == 0:
    sys.exit(0)

if "retry" in config and config["retry"] > 0:
    RETRY_NUM = int(config["retry"])

# only support http(s) proxy
if "proxyServer" in config and type(config["proxyServer"]) == dict:
    PROXY = config["proxyServer"]

# sleep
if "waitTime" in config and 0 < config["waitTime"] <= 24:
    time.sleep(get_randint(0, config["waitTime"] * 60 * 60))

params = config["domains"]
# %%
for i in range(len(params)):
    wrapper(params[i])
# %%
# wrapper(params[1])