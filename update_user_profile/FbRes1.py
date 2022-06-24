#!/usr/bin/env python
#-*- coding: UTF-8 -*-
from res_methods import Actions,BaseQueries
from datetime import datetime,timedelta
from gologin import GoLogin
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import os, time, sys, json
import pymysql
import random
import requests
from bs4 import BeautifulSoup



stream_name = str(os.path.basename(sys.argv[0]).split(".py")[0])
stream = int(stream_name.split("FbRes")[1])
print("stream", stream)


user_id = 1000
p_id = 10

BaseQ = BaseQueries()
Action = Actions()




#########################################1.BROWSER_LOADING_START
def loading_browser(stream, stream_name):
    display = Display(visible=0, size=(1600, 900))
    display.start()

    token = BaseQ.get_GoToken()
    profilePort = BaseQ.get_PofileIdPort(stream_name)
    for pr in profilePort:
        profile_id=str(pr[0])
        port =str(pr[1])
        name =str(pr[2])
        proxy_type=str(pr[3])
        priority = int(pr[4])

    print("token", token)
    print("profile_id", profile_id)
    print("port", port)
    print("name", name)

    gl = GoLogin({
        'token':token,
        'profile_id': profile_id,
        'port':port
        })

    chrome_driver_path = 'chromedriver'

    debugger_address = gl.start()
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", debugger_address)
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)
    # driver.set_window_size(1600, 900)
    time.sleep(3)

    driver.get("http://www.facebook.com")

    time.sleep(5)
    try:
        driver.find_element_by_xpath("//button[@data-testid='royal_login_button']").click()
        time.sleep(2)
    except Exception as e:
        print("login_click_error", e)

    driver.save_screenshot('facebook_resource/logs/%s.png'%(stream))
    # gl.stop()
    # display.stop()
    return (display, driver, priority, proxy_type,gl)




##################################GET_PROFILE
load = loading_browser(stream, stream_name)
display = load[0]
driver = load[1]
priority = load[2]
proxy_type = load[3]
gl = load[4]





##################################GET_TASKS
getTasks = BaseQ.get_tasks_res_social()
for task in getTasks:
    print("Sleep: 10-15")
    time.sleep(random.randint(10,15))
    try:
        res_id = task[0]
        s_id = task[1]
        resource_name = task[2]
        link = task[3]
        image_profile = task[4]
        members_count = task[5]
        friends_count = task[6]
        worker = task[7]
        closed = task[8]
        country_id = task[9]
        region_id = task[10]
        city_id = task[11]
        stability = task[12]

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("Время: ", now)
        print("Res_id: ", res_id)

        print("\nДанные из БД!_________________")
        print("stability: ", stability)
        print("worker: ", worker)
        print("closed: ", closed)
        print("friends_count: ", friends_count)
        print("members_count: ", members_count)
        print("s_id: ", s_id)
        print("resource_name: ", resource_name)
        print("link: ", link)
        print("image_profile: ", image_profile)
        print("country_id: ", country_id)
        print("region_id: ", region_id)
        print("city_id: ", city_id)
        
        print("\nСравнение с Новыми Данными!___________________________")
        link = 'https://www.facebook.com/'+str(s_id)
        d = Action.get_data(driver, link, res_id)
        data = d[0]
        current_link=d[1]


        if "Этот контент сейчас недоступен" in str(data):
            print("Ресурс видимо не работает: ", res_id, link)

        else:
            new_resource_name = Action.get_resource_name(data)
            new_members_count = Action.get_members_count(driver, data)
            new_closed = Action.get_closed(data)
            new_kind_s_id = Action.get_res_type(data)
            new_image = Action.get_resource_image(data)
            new_friends_count=Action.get_friends_count(data)

            loc_change=0

            if new_kind_s_id!='KindError':
                new_kind = new_kind_s_id[0]
                new_s_id = new_kind_s_id[1]
                if new_members_count!='MemersCountError':
                    if new_resource_name!='ResNameError':
                        if new_image!='ResImageError':
                            if str(s_id)==str(new_s_id):

                                print("current_link", current_link)
                                print("new_kind", new_kind)

                                if new_kind==1:
                                    new_loc_link = current_link+'/about'

                                    new_loc_link= new_loc_link.replace("//",'/')
                                    print("new_loc_link", new_loc_link)

                                    driver.get(new_loc_link)
                                    time.sleep(random.randint(3,5))
                                    loc_data = driver.page_source
                                    driver.save_screenshot('facebook_resource/logs/group.png')
                                    text = str(loc_data).replace("!--", "")
                                    loc_data = BeautifulSoup(text, 'html.parser')
                                    location = Action.get_group_location(loc_data)

                                if new_kind==2:
                                   
                                    if "profile" in str(current_link):
                                        new_loc_link = current_link+'&sk=about_places'
                                    else:
                                        new_loc_link = current_link+'/about_places'

                                    new_loc_link= new_loc_link.replace("//",'/')                                        
                                    print("new_loc_link", new_loc_link)

                                    driver.get(new_loc_link)
                                    time.sleep(random.randint(3,5))
                                    loc_data = driver.page_source
                                    driver.save_screenshot('facebook_resource/logs/user.png')
                                    text = str(loc_data).replace("!--", "")
                                    loc_data = BeautifulSoup(text, 'html.parser')
                                    location = Action.get_user_location(loc_data)

                                if new_kind==3:
                                    new_loc_link = current_link+'/about'
                                    new_loc_link= new_loc_link.replace("//",'/')
                                    print("new_loc_link", new_loc_link)


                                    driver.get(new_loc_link)
                                    time.sleep(random.randint(3,5))
                                    loc_data = driver.page_source
                                    driver.save_screenshot('facebook_resource/logs/page.png')
                                    text = str(loc_data).replace("!--", "")
                                    loc_data = BeautifulSoup(text, 'html.parser')
                                    location = Action.get_page_location(loc_data)

                                new_country_id = 222
                                new_region_id = 0
                                new_city_id = 0

                                if location!='LocationError':
                                    print("Location", location)
                                    locations = BaseQ.check_locations_by_kz(location)
                                    new_country_id = locations[0]
                                    new_region_id = locations[1]
                                    new_city_id = locations[2]

                                else:
                                    print("LocationError")


                                print("new_country_id", new_country_id, new_region_id, new_city_id)

                                if new_country_id==222:
                                    locations = BaseQ.check_locations_by_kz(new_resource_name)
                                    new_country_id = locations[0]
                                    new_region_id = locations[1]
                                    new_city_id = locations[2]


                                if int(country_id)!=int(new_country_id):
                                    if new_country_id!=222:
                                        loc_change=1
                                        send_country_id = new_country_id
                                        print("Поменялась страна", country_id, "-->>", send_country_id)
                                    else:
                                        send_country_id = country_id
                                else:
                                    send_country_id = country_id


                                if int(region_id)!=int(new_region_id):
                                    if int(new_region_id)!=0:
                                        loc_change=1
                                        send_region_id = new_region_id
                                        print("Поменялся регион", region_id, "-->>", send_region_id)
                                    else:
                                        send_region_id = region_id
                                else:
                                    send_region_id = region_id


                                if int(city_id)!=int(new_city_id):
                                    if int(new_city_id)!=0:
                                        loc_change=1
                                        send_city_id = new_city_id
                                        print("Поменялся город", city_id, "-->>", send_city_id)
                                    else:
                                        send_city_id = city_id
                                else:
                                    send_city_id = city_id


                                if new_members_count==0:
                                    new_members_count = members_count


                                new_link = 'https://www.facebook.com/'+str(new_s_id)
                                print("new_worker: ", worker, " --> ",new_kind)
                                print("new_closed: ", closed, " --> ",new_closed)
                                print("new_friends_count: ", friends_count, " --> ",new_friends_count)
                                print("new_members_count: ", members_count, " --> ",new_members_count)
                                print("new_s_id: ", s_id, " --> ", new_s_id)
                                print("new_resource_name: ", resource_name, " --> ",new_resource_name)
                                print("new_link: ", link, " --> ",new_link)
                                print("new_country_id: ", country_id, " --> ", new_country_id)
                                print("new_region_id: ", region_id, " --> ",  new_region_id)
                                print("new_city_id: ", city_id, " --> ",   new_city_id)
                                print("new_image_profile: ", image_profile, "\n            --> ",new_image)
                                print("________________________________________________________________\n")

                                
                                BaseQ.update_res_social(send_country_id,send_region_id,send_city_id,new_s_id, new_closed, new_friends_count, int(new_members_count), new_resource_name, new_link, new_image)
                                res_id = BaseQ.get_res_id(new_s_id)[0][0]
                                BaseQ.insert_facebook_resources(send_country_id,send_region_id,send_city_id,link,res_id,s_id,new_kind,new_closed,new_resource_name,new_image,int(new_members_count),int(new_friends_count),new_link)
                                
                                if new_country_id!=222:
                                    if loc_change==1:
                                        BaseQ.update_sphinx_locations(country_id,region_id,city_id,new_country_id,new_region_id,new_city_id,res_id)
                            else:
                                print("Str!=NEWStr")
                        else:
                            print("ResImageError")
                    else:
                        print("ResNameError")
                else:
                    print ("MemersCountError")
            else:
                print ("KindError")

    except Exception as e:
        print("TaskError", e)


gl.stop()
driver.close()
display.stop()
