import time
import re
from datetime import datetime, timedelta
import random
import pymysql
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
import requests
from metrics_methods import Parsing, Queries, Metrics
from selenium.common import exceptions
import pickle
import json

from bs4 import BeautifulSoup
from pyvirtualdisplay import Display

from connects1 import DB
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from gologin import GoLogin

db = DB()
m = Metrics()

p = Parsing()
q = Queries()

display = Display(visible=0, size=(1920, 1080))
display.start()

token = ""

profilePort = q.get_PofileIdPort()
for pr in profilePort:
    profile_id=str(pr[0])
    port =str(pr[1])
    name =str(pr[2])
    id_2 =pr[3]

q.UpdateUseDate(id_2)

print("token", token)
print("profile_id", profile_id)
print("port", port)
print("name", name)


gl = GoLogin({
    'token':token,
    'profile_id': profile_id,
    'port': port
    })


chrome_driver_path = 'chromedriver'

debugger_address = gl.start()
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", debugger_address)
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

driver.get("http://www.facebook.com")
driver.save_screenshot('/fb_metrics/login.png')

def start(stream):
    result = m.get_posts(stream)
    

    ids = result[0]
    posts = result[1]

    status_200 = []
    ids = ','.join(str(e) for e in ids)
    

    print("ids", ids)
    print("posts", posts)
    print("Время",datetime.now())


    if ids:
        print("ids", ids)
        m.start_stream(ids)


        if posts ==[]:
            m.update_finish_501(ids)

        else:
            for p in posts:
                time.sleep(random.randint(5, 10))
                post_id = p[1]
                post_link = p[2]
                item_id = p[3]
                metircs = []
                # proxy = proxies[random.randint(0, len(proxies) - 1)][0]
                # proxy = proxies[0][0]
                
                post_link = str(post_link).replace("?","").replace("https:/w", "https://w").replace("https:/f", "https://f")
                print("post_id", stream, post_id, post_link)
                try:
                    data = m.get_metrics(post_link, driver, item_id)
        
                    status_code = int(data[0])
                    likes_count = int(data[1])
                    repost_count = int(data[2])
                    comments_count = int(data[3])

                    print("status_code", status_code, post_id)
                    print("likes_count", likes_count)
                    print("repost_count", repost_count)
                    print("comments_count", comments_count)

                    if likes_count > 0 or repost_count > 0 or comments_count > 0:
                        metircs.append((post_id, likes_count, comments_count,
                                        repost_count))

                    if metircs != []:
                        m.insert_metrics_all(metircs)

                    if status_code != 200:
                        m.update_finish(post_id, status_code)
                    else:
                        status_200.append(post_id)

                except Exception as e:
                    print(e)

                print("_______________\n")

            if status_200 != []:
                status_200 = ','.join(str(e) for e in status_200)
                m.update_finish_200(status_200)

            time.sleep(random.randint(5, 10))
    else:
        print("sleep_3")
        time.sleep(3)


def ready(stream):
    # while True:
    start(stream)



ready(1)
# thread1 = Thread(target=ready, args=(1,))
# # thread2 = Thread(target=ready, args=(2,))
# # thread3 = Thread(target=ready, args=(3,))

# thread1.start()
# # thread2.start()
# # thread3.start()

# thread1.join()
# # thread2.join()
# # thread3.join()

# print("--- %s seconds ---" % (time.time() - start_time))
