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
import time
from file_read_backwards import FileReadBackwards
# %%
warnings.filterwarnings('ignore') #ignore std warning，don't mind

HEADER = {
    "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
    "dnt": "1",
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

log_file = os.path.join(PATH, 'checkin.log')
fh = logging.FileHandler(encoding='utf-8', mode='a', filename=log_file)
logging.basicConfig(
    handlers=[fh],
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
        end = len(url)

    return url[start + 2:end]

def is_checked(url):
    flag = False
    today = time.strftime("%Y-%m-%d",time.localtime(time.time()))
    with FileReadBackwards(log_file, encoding="utf-8") as frb:
        for line in frb:
            if not line.startswith(today):
                flag = False
                break
            elif line.find(extract_domain(url))!=-1 and line.find("INFO")!=-1:
                flag = True
                break
    return flag

def get_formhash():
    # TODO, how?
    pass

def checkin(url, headers, form_data, retry, proxy=False):
    print(headers)
    try:
        if proxy:
            response = requests.post(url, headers=headers, proxies=PROXY, verify=False)
        else:
            response = requests.post(url, headers=headers, data=form_data)
        print("+++++++++++++++++++++++++++")
        print(response.text)
        if response.status_code == 200:
            # TODO 
            if re.findall("已签|已经签到|签过到", response.text) != []:
                logging.info("已经签到 URL: {}".format(extract_domain(url)))
            elif re.findall("签到成功", response.text) != []:
                logging.info("签到成功 URL: {}".format(extract_domain(url)))
            else:
                logging.error("签到失败 URL: {}, 返回内容: {}".format(extract_domain(url), response.text))

            return 

    except RequestException as e:
        logging.error(str(e))
        retry -= 1

        if retry > 0:
            time.sleep(get_randint(30, 60 * 60))
            checkin(url, headers, retry, proxy)

        logging.error(u"签到失败 URL: {}".format(extract_domain(url)))

def flow(domain, params, headers, checkin_url, proxy=False):
    domain = domain.strip()# remvoe space in start and tail
    regex = "(?i)^(https?:\\/\\/)?(www.)?([^\\/]+\\.[^.]*$)"
    flag = re.search(regex, domain)

    if not flag:
        return False

    cookie = params["cookies"]
    headers["cookie"] = cookie
    form_data = params["form_data"]
    headers["origin"] = domain
    if not is_checked(domain):
        checkin(checkin_url, headers, form_data, RETRY_NUM, proxy)
    else:
        logging.info("已经签到 URL: {}".format(extract_domain(domain)))

def wrapper(args):
    flow(args["domain"], args["param"], HEADER, args["checkin_url"], args["proxy"])
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
# wrapper(params[3])

# %%
