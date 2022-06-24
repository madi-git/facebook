#!/usr/bin/env python
#-*- coding: UTF-8 -*-
import os, time,re

from selenium.webdriver.common.keys import Keys

from connects import DB
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
import pymysql
import json
import dateparser
import requests
import random
from dateutil.relativedelta import relativedelta, MO
from datetime import date
from locations.countries import full_countries
from locations.regions import full_regions
from locations.cities import full_cities
from locations.transcription import legend


db = DB()

class Actions():
    def remove_emoji(self, string):
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   u"\U00002500-\U00002BEF"  # chinese char
                                   u"\U00002702-\U000027B0"
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   u"\U0001f926-\U0001f937"
                                   u"\U00010000-\U0010ffff"
                                   u"\u2640-\u2642"
                                   u"\u2600-\u2B55"
                                   u"\u200d"
                                   u"\u23cf"
                                   u"\u23e9"
                                   u"\u231a"
                                   u"\ufe0f"  # dingbats
                                   u"\u3030"
                                   "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', string)




    def get_data(self, driver, link, res_id):
        print("Получаю данные ресурса")
        driver.get(link)
        time.sleep(random.randint(20,25))
        html = driver.find_element_by_tag_name('html')
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(random.randint(3,5))

        driver.save_screenshot('facebook_resource/logs/%s.png'%(res_id))

        data = driver.page_source
        text = str(data).replace("!--", "")
        data = BeautifulSoup(text, 'html.parser')

        current_link = driver.current_url

        return (data, current_link)

    def get_resource_image(self, data):
        print("Получаю картинку ресурса")
        try:
            image = data.find_all("div", {"class": "b3onmgus e5nlhep0 ph5uu5jm ecm0bbzt spb7xbtv bkmhp75w emlxlaya s45kfl79 cwj9ozl2"})
            resource_image = image[0].find_all("image")[0].get('xlink:href')
        except:
            try:
                image = data.find_all("div", {"class": "o8rfisnq j83agx80 cbu4d94t tvfksri0 aov4n071 bi6gxh9e l9j0dhe7"})
                resource_image = image[0].find_all("image")[0].get('xlink:href')
            except:
                try:
                    image = data.find_all("div", {"class": "gs1a9yip ow4ym5g4 auili1gw j83agx80 cbu4d94t buofh1pr g5gj957u i1fnvgqd oygrvhab cxmmr5t8 hcukyx3x kvgmc6g5 tgvbjcpo hpfvmrgz qt6c0cv9 rz4wbd8a a8nywdso jb3vyjys du4w35lb i09qtzwb rq0escxv n7fi1qx3 pmk7jnqg j9ispegn kr520xx4"})
                    resource_image = image[0].find_all("img")[0].get('src')
                except  Exception as e:
                    print("get_resource_image_error", e)
                    return "ResImageError"
            
        return resource_image


    def get_resource_name(self, data):
        print("Получаю название ресурса")
        resource_name=''
        try:
            # res_name = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql b0tq1wua a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb h6olsfn3 m6dqt4wy h7mekvxk hnhda86s oo9gr5id hzawbc8m')
            res_name = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 l1jc4y16 rwim8176 mhxlubs3 p5u9llcw hnhda86s oo9gr5id hzawbc8m')
            # print("res_name", res_name[0])
            for x in res_name:
                resource_name = x.getText()
                resource_name = str(resource_name).replace("< -->", '')
                # print("resource_name1", resource_name)

            if resource_name=='':
                # res_name = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql b0tq1wua a8c37x1j keod5gw0 nxhoafnm aigsh9s9 qg6bub1s fe6kdd0r mau55g9w c8b282yb teo7jy3c mhxlubs3 p5u9llcw hnhda86s oo9gr5id oqcyycmt')
                res_name = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 embtmqzv hrzyx87i m6dqt4wy h7mekvxk hnhda86s oo9gr5id hzawbc8m')
                # print("res_name", res_name[0])
                for x in res_name:
                    resource_name = x.getText()
                    resource_name = str(resource_name).replace("< -->", '')
                    # print("resource_name2", resource_name)

        except Exception as e:
            print("get_resource_name_error", e)
            return "ResNameError"
        
        resource_name = self.remove_emoji(resource_name)

        return resource_name



    def get_members_count(self, driver, data):
        print("Получаю подписчиков ресурса")
        try:
            members_count = 0
            # items = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql b0tq1wua jq4qci2q a3bd9o3v knj5qynh oo9gr5id')
            items = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh jq4qci2q a3bd9o3v b1v8xokw oo9gr5id')
            for item in items:
                for x in ['Подписан ', 'Подписаны ']:
                    if x in str(item):
                        try:
                            count = item.text
                            members_count = str(count).split(x)[1].split(" человек")[0]
                            members_count = str(members_count).replace("тыс.", '000')
                            
                            word_list = members_count.split()
                            members_count = int(''.join(str(e) for e in word_list))
                        except Exception as e:
                            print("word_list_error1", e)


            if members_count==0:
                try:
                    items_2 = data.find_all("div", class_='rq0escxv l9j0dhe7 du4w35lb j83agx80 cbu4d94t pfnyh3mw d2edcug0 hpfvmrgz n8tt0mok hyh9befq r8blr3vg jwdofwj8')
                    for item2 in items_2:
                        if "Участники: " in str(item2):
                            try:
                                count2 = item2.text
                                members_count2 = str(count2).split("Участники: ")[1].split("<")[0].replace("тыс.", '000')
                                if "," in str(members_count2):
                                    members_count2=members_count2.replace(",", '').replace("000", '00')


                                word_list2 = members_count2.split()
                                # print("word_list", word_list2)
                                members_count = ''.join(str(e) for e in word_list2)
                                # print("members_count2", members_count)
                            except Exception as e:
                                print("word_list_error2", e)
                except Exception as e:
                    print("get_members_count_error", e)


            if members_count==0:
                try:
                    # members = data.find_all("meta", {"name": "description"})
                    # members = data.find_all("div", class_='rq0escxv l9j0dhe7 du4w35lb j83agx80 cbu4d94t pfnyh3mw d2edcug0 hpfvmrgz n8tt0mok hyh9befq r8blr3vg jwdofwj8')
                    members = data.find_all("a", class_='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gpro0wi8 m9osqain lrazzd5p')
                    for mem in members:
                        # count = str(mem.get('content'))
                        count = mem.text
                        # if "участников" in count:
                        if "участник(-ов)" in count:
                            members_count = str(count).split(" участник(-ов)")[0]
                            members_count = str(members_count).replace(",", '')
                            members_count = str(members_count).replace("тыс.", '00')

                            word_list = members_count.split()
                            members_count = int(''.join(str(e) for e in word_list))
                except Exception as e:
                    print("get_members_count_error", e)



            if members_count==0:
                try:
                    members_1 = data.find_all("span", class_='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d3f4x2em mdeji52x a5q79mjw g1cxx5fr b1v8xokw m9osqain')
                    for mem_1 in members_1:
                        # if "подписчики: < -->" in str(mem_1):
                        count_1 = mem_1.text
                        if "подписчики: < -->" in str(count_1):
                            members_count = str(count_1).split("подписчики: < -->")[1].split(" • подписки: < -->")[0]
                            # print("TUTATUT USERID ПОДПИСЧИКИ: ", members_count)
                            if "," in members_count:
                                members_count = str(members_count).replace(",", '')
                                members_count = str(members_count).replace("тыс.", '00')

                                word_list = members_count.split()
                                # print("word_listkok ", word_list)
                                members_count = int(''.join(str(e) for e in word_list))
                                # members_count = int(members_count)

                            if "," not in members_count:
                                members_count = str(members_count).replace("тыс.", '000')
                                word_list = members_count.split()
                                members_count = int(''.join(str(e) for e in word_list))

                except Exception as e:
                    print("get_members_count_error66", e)



            if members_count ==0:
                mdata = ["d2edcug0 hpfvmrgz qv66sw1b c1et5uql b0tq1wua a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d9wwppkn fe6kdd0r mau55g9w c8b282yb hrzyx87i jq4qci2q a3bd9o3v knj5qynh oo9gr5id hzawbc8m",
                         "d2edcug0 hpfvmrgz qv66sw1b c1et5uql b0tq1wua jq4qci2q a3bd9o3v knj5qynh m9osqain",
                         "d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d3f4x2em iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]
                for m in mdata:
                    items = data.find_all("span", class_=m)
                    for item in items:
                        if "Подписчики: " in str(item):
                            try:
                                count = item.text
                                # print("count", count)
                                members_count = str(count).split("Подписчики: ")[1].split(" человек")[0]
                                # print("members_count", members_count)
                                members_count = str(members_count).replace("тыс.", '000')
                                word_list = members_count.split()
                                # print("word_list", word_list)
                                members_count = int(''.join(str(e) for e in word_list))
                            except Exception as e:
                                print("word_list_error4", e)

                        if "подписчик" in str(item) and "подписчики: " not in str(item):
                            try:
                                count = item.text
                                # print("count", count)
                                members_count = str(count).split("подписчик")[0]
                                members_count = str(members_count).replace("тыс.", '000')
                                # print("members_count", members_count)
                                word_list = members_count.split()
                                # print("word_list", word_list)
                                members_count = int(''.join(str(e) for e in word_list))
                            except Exception as e:
                                print("word_list_error3", e)

        except Exception as e:
            print("get_members_count_error", e)
            return "MembersCountError"
        return members_count


    def get_friends_count(self, data):
        print("Получаю друзей ресурса")
        friends_count = 0
        try:
            # items = data.find_all("span", class_="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7")
            items = data.find_all("span", class_="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ojkyduve")
            # items = data.find_all("span", class_="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d3f4x2em mdeji52x a5q79mjw g1cxx5fr b1v8xokw m9osqain")
            for item in items:
                # print("item",item)
                if "Друзья:" in str(item):
                    try:
                        count = item.text
                        # print("count", count)
                        friends_count = str(count).split("Друзья:")[1]
                        # print("friends_count", friends_count)
                        friends = friends_count.split()
                        friends_count = int(''.join(str(e) for e in friends))
                    except Exception as e:
                        print("get_friends_error", e)
                        return "FriendError"
        except Exception as e:
            print("get_friends_count_error", e)
            return "FriendError"
        return friends_count


    def get_res_type(self, data):
        print("Получаю тип ресурса")
        s_id=0
        
        try:
            kinds = str(data).split("\"props\":{\"")[1].split("}")[0]
            if "groupID" in str(kinds):
                kind = 1
                s_id = str(kinds).split("groupID\":\"")[1].split("\"")[0]
            if "userID" in str(kinds):
                kind = 2
                s_id = str(kinds).split("userID\":\"")[1].split("\"")[0]
            if "pageID" in str(kinds):
                kind = 3
                s_id = str(kinds).split("pageID\":\"")[1].split("\"")[0]

            kind = int(kind)
        except Exception as e:
            print("get_res_type_error", e)
            return "KindError"
        return (kind, s_id)



    def get_closed(self, data):
        print("Получаю закрытость ресурса")
        if "Закрытая группа" in str(data):
            closed =1
        elif "Общедоступная группа" in str(data):
            closed =0
        else:
            closed= 0
        return closed



    def get_group_location(self, data):
        
        try:
            items = data.find_all("div", class_="rq0escxv l9j0dhe7 du4w35lb j83agx80 cbu4d94t pfnyh3mw d2edcug0 aahdfvyu tvmbv18p")
            for item_ in items:
                for item in item_:
                    for l in item:
                        try:
                            if "<strong>" in str(l):
                                try:
                                    loc_name = str(l.span.text)
                                    print("loc_name: ", loc_name)
                                    print("\n")
                                    return loc_name
                                    break
                                except:
                                    pass
                        except:
                            pass
        except Exception as e:
            print("get_group_location_error", e)
            return "LocationError"
        return ""




    def get_user_location(self, data):
        
        try:
            items = data.find_all("div", class_="dati1w0a tu1s4ah4 f7vcsfb0 discj3wi")
            for item_ in items:
                for item in item_:
                    for l in item:
                        try:
                            loc_name = l.find_all("span", "nc684nl6")[0].text
                            loc_type=l.find_all("span", "j5wam9gi e9vueds3 m9osqain")[0].text
                            print("loc_type: ", loc_type)
                            print("loc_name: ", loc_name)
                            print("\n")
                            return loc_name
                            break
                        except Exception as e:
                            pass
        except Exception as e:
            print("get_user_location_error", e)
            return "LocationError"
        return ""



    def get_page_location(self, data):
        
        try:
            items = data.find_all("div", class_="l9j0dhe7 dhix69tm wkznzc2l p5pk11vy o9dbymsk j83agx80 kzx2olss aot14ch1 p86d2i9g beltcj47 m8zidbmv ccq6eem2 ellw4o9j kzizifcz g6srhlxm")
            for item in items:
                try:
                    l_name = item.find_all("span", "d2edcug0 hpfvmrgz qv66sw1b c1et5uql b0tq1wua jq4qci2q a3bd9o3v knj5qynh py34i1dx")
                    loc_name = str(l_name[0].text).strip("\n\r\t")
                    return loc_name
                    break
                except Exception as e:
                    print(e)
        except Exception as e:
            print("get_page_location_error", e)
            return "LocationError"
        return ""







class BaseQueries():
    def update_sphinx_locations(self,old_country_id,old_region_id,old_city_id,new_country_id,new_region_id,new_city_id,res_id):
        db.q_new("social_services", 'insert', """INSERT IGNORE INTO locations (res_id, 
                                                                                      type, 
                                                                                      post_id, 
                                                                                      old_country_id, 
                                                                                      old_region_id, 
                                                                                      old_city_id,
                                                                                      new_country_id,
                                                                                      new_region_id,
                                                                                      new_city_id,
                                                                                      info_update) 
                                                 VALUES ({0},{1},{2},{3},{4},{5},{6},{7},{8},NOW())""".format(res_id,
                                                                                                                1,
                                                                                                                0,
                                                                                                                old_country_id, 
                                                                                                                old_region_id, 
                                                                                                                old_city_id,
                                                                                                                new_country_id,
                                                                                                                new_region_id,
                                                                                                                new_city_id))



    def check_locations_by_db(self, location_def, location, new_country_id, new_region_id, new_city_id):
        def latinizator(letter, dic):
            for i, j in dic.items():
                letter = letter.replace(i, j)
            return letter

        location_ = db.q_new('social_services', 'select', 
                             """SELECT id, country_id,region_id,name 
                                FROM `cities` 
                                WHERE name NOT LIKE '%район%' 
                                AND country_id IN (40,57) AND id NOT IN (1,2, 22)""")


        for loc in location_:
            city_id=loc[0]
            country_id=loc[1]
            region_id=loc[2]
            city_name=loc[3]

            # print("city_imas,", city_id)
            # print("country_imas",country_id)
            # print("region_imas",region_id)
            # print("city_name_imas",city_name)
            # print("location_def",location_def)
            # print("location",location)

            imas_name = str(city_name).lower()
            lat_name=str(latinizator(imas_name, legend)).lower()

            if len(imas_name) > 2:
                if imas_name != 'арал':

                    if (imas_name in location) or (lat_name in location):
                        
                        print("Название ресурса встретилось", imas_name)
                        # new_city_id = city_id
                        # new_country_id=country
                        # new_region_id=region

                        if city_id==75:
                            if ("Чита " in location_def):
                                print("Название ресурса встретилось", imas_name)
                                new_city_id = city_id
                                new_country_id=country_id
                                new_region_id=region_id
                            else:
                                new_city_id = 0
                                new_region_id = 0
                                new_country_id = 222

                        elif city_id==5:    
                            if not ("семейн" in location):
                                print("Название ресурса встретилось", imas_name)
                                new_city_id = city_id
                                new_country_id=country_id
                                new_region_id=region_id
                            else:
                                new_city_id = 0
                                new_region_id = 0
                                new_country_id = 222

                        else:
                            print("Название ресурса встретилось", imas_name)
                            new_city_id = city_id
                            new_country_id=country_id
                            new_region_id=region_id

        return (new_country_id, new_region_id, new_city_id)





    def check_locations_by_kz(self, location_def):
        location = str(location_def.lower())
        new_country_id =222
        new_region_id =0
        new_city_id =0

        kaz_letters=['ә', 'ғ', 'қ', 'ң', 'ө', 'ұ', 'ү']
        for l in kaz_letters:
            if (l in location):
                new_country_id=57


        for country in full_countries:
            country_low = str(country.lower())

            if (country_low in location):
                new_city_id = full_countries[country]['new_city_imas']
                new_country_id = full_countries[country]['new_country_imas']
                new_region_id=full_countries[country]['new_region_imas']


        for region in full_regions:
            region_low = region.lower()
            
            if (region_low in location):
                if region_low== "ско":
                    if (" СКО " in location_def):
                        new_city_id = full_regions[region]['new_city_imas']
                        new_country_id = full_regions[region]['new_country_imas']
                        new_region_id=full_regions[region]['new_region_imas']
                elif region_low == "зко":
                    if (" ЗКО " in location_def):
                        new_city_id = full_regions[region]['new_city_imas']
                        new_country_id = full_regions[region]['new_country_imas']
                        new_region_id=full_regions[region]['new_region_imas']
                elif region_low == "вко":
                    if (" ВКО " in location_def):
                        new_city_id = full_regions[region]['new_city_imas']
                        new_country_id = full_regions[region]['new_country_imas']
                        new_region_id=full_regions[region]['new_region_imas']
                else:
                    new_city_id = full_regions[region]['new_city_imas']
                    new_country_id = full_regions[region]['new_country_imas']
                    new_region_id=full_regions[region]['new_region_imas']


        for city in full_cities:
            city_low = city.lower()
            if (city_low in location):
                if city_low=='астан':
                    if not ('дастан' in location):
                        new_city_id = full_cities[city]['new_city_imas']
                        new_country_id = full_cities[city]['new_country_imas']
                        new_region_id=full_cities[city]['new_region_imas']
                elif city_low=='ukg':
                    if (" ukg " in location):
                        new_city_id = full_cities[city]['new_city_imas']
                        new_country_id = full_cities[city]['new_country_imas']
                        new_region_id=full_cities[city]['new_region_imas']
                else:
                    new_city_id = full_cities[city]['new_city_imas']
                    new_country_id = full_cities[city]['new_country_imas']
                    new_region_id=full_cities[city]['new_region_imas']

        print("new_city_imas",new_city_id)
        print("new_country_imas",new_country_id)
        print("new_region_imas",new_region_id)

        data = self.check_locations_by_db(location_def,location, new_country_id, new_region_id, new_city_id)
        return data




    def finish_not_found(self, task_id):
        return db.q_new('imasv2', 'insert', """UPDATE facebook_resources 
                                               SET s_id='not_found'
                                               WHERE id = {}""".format(task_id))


    def start_task(self, task_id):
        return db.q_new('imasv2', 'insert', """UPDATE facebook_resources 
                                           SET check_date=NOW()
                                           WHERE id = {}""".format(task_id))

    def task_finish(self, new,new_country_id,new_region_id,new_city_id,res_id, task_id, new_s_id, new_kind, new_closed, new_friends_count, new_members_count, new_resource_name, new_link, new_image):
        
        q = """UPDATE facebook_resources 
               SET check_date=NOW(), 
                   res_id={0}, 
                   kind={1}, 
                   is_closed={2}, 
                   friends_count={3}, 
                   members={4}, 
                   resource_name='{5}', 
                   new_link='{6}', 
                   image_profile='{7}', 
                   s_id = '{8}',  
                   country_id={9}, 
                   region_id={10}, 
                   city_id={11},
                   new='{13}'
               WHERE type=2 AND id ={12}""".format(res_id, 
                                                   new_kind, 
                                                   new_closed, 
                                                   new_friends_count, 
                                                   new_members_count, 
                                                   new_resource_name, 
                                                   new_link, 
                                                   new_image, 
                                                   new_s_id, 
                                                   new_country_id,
                                                   new_region_id,
                                                   new_city_id,
                                                   task_id,
                                                   new)
        return db.q_new('social_services', 'insert', q)





    def add_links(self, links):
        add_links = []
        for link in links:
            add_links.append((0,2, link))
        return db.q_new("social_services", 'insert', """INSERT IGNORE INTO facebook_resources (from_db, type, link) 
                                                          VALUES (%s,%s, %s)""", 1, add_links)


    def add_res_ids(self, res_id, priority):
        return db.q_new("social_services", 'insert', """INSERT IGNORE INTO facebook_users_groups (res_id, priority) 
                                                          VALUES ({0}, {1})""".format(res_id, priority))


    def get_res_ids(self, date_):
        return db.q_new("imasv2", 'select', """SELECT res_id, new_link 
                                                FROM `facebook_resources` 
                                                WHERE check_date>'{0}' 
                                                AND res_id>0
                                                AND kind=2 ORDER BY `id` DESC""".format(date_))



    def get_add_links(self):
        return db.q_new("imasv2", 'select', """SELECT id, link
                                               FROM `facebook_resources` 
                                               -- WHERE id IN (1014)
                                               -- WHERE res_id = 341634
                                               WHERE `type` = 2 AND `from_db`=0
                                               AND check_date= '0000-00-00 00:00:00'
                                               -- WHERE `country_id` = 222
                                               ORDER BY `id` ASC LIMIT 8""")

   


    #madi added workers (1,2,3)
    def get_tasks_res_social(self,):
        return db.q("imasv2", 'select', """SELECT id, s_id, resource_name, link, image_profile, members, friends_count, worker, is_closed, country_id, region_id, city_id, stability
                                           FROM `resource_social` 
                                           WHERE `type` = 2
                                           -- AND id IN (507786434)
                                           AND info_check =0
                                           AND worker in (1,2,3)
                                           AND stability=1
                                           ORDER BY `id` DESC
                                           LIMIT 10""")

    
    def check_res_in_res_social(self, s_id):
        return db.q("imasv2", 'select', """SELECT id, s_id, resource_name, link, image_profile, members, friends_count, worker, is_closed, country_id, region_id, city_id, stability
                                           FROM `resource_social` 
                                           WHERE `type` = 2 
                                           AND  s_id = {} 
                                           ORDER BY `id` ASC""".format(s_id))


    def get_res_id(self, s_id):
        return db.q("imasv2", 'select', """SELECT id
                                           FROM `resource_social` 
                                           WHERE `type` = 2 
                                           AND  s_id = {} 
                                           ORDER BY `id` ASC""".format(s_id))


    def insert_facebook_resources(self,new_country_id,new_region_id,new_city_id,link,res_id,s_id,new_kind,new_closed,resource_name,image_profile,new_members_count,friends_count,new_link):
        q = """INSERT IGNORE INTO facebook_resources (check_date,
                                                      from_db,
                                                      new,
                                                      type,
                                                      link,
                                                      res_id,
                                                      s_id,
                                                      kind,
                                                      is_closed,
                                                      resource_name,
                                                      image_profile,
                                                      members,
                                                      friends_count,
                                                      new_link,
                                                      country_id,
                                                      region_id,
                                                      city_id) 
                           VALUES (NOW(),%d,%d,%d,'%s',%d,'%s',%d,%d,'%s','%s',%d,%d,'%s','%s','%s','%s') 
                           ON DUPLICATE KEY UPDATE friends_count=VALUES(friends_count), country_id=VALUES(country_id),region_id=VALUES(region_id), city_id=VALUES(city_id), members=VALUES(members), resource_name=VALUES(resource_name)"""%(1,0,2,link,res_id,s_id,new_kind,new_closed,resource_name,image_profile,new_members_count,friends_count,new_link,new_country_id,new_region_id,new_city_id)
        return db.q_new('imasv2', 'insert', q)



    def add_resource_social(self, country_id,region_id,city_id, s_id, worker, is_closed, friends_count, members, resource_name, link, image_profile):
        stability=1
        info_check=1
        type_=2

        q = """INSERT IGNORE INTO resource_social (type,
                                                   country_id,
                                                   region_id,
                                                   city_id,
                                                   s_id,
                                                   worker,
                                                   is_closed,
                                                   friends_count,
                                                   members,
                                                   resource_name,
                                                   link,
                                                   image_profile,
                                                   stability, 
                                                   info_check, 
                                                   start_date_imas,
                                                   date_enable,
                                                   datetime_enable) 
               VALUES (%d,%d,%d,%d,'%s',%d,%d,%d,%d,'%s','%s','%s',%d,%d,NOW(),NOW(),NOW())"""%(type_,
                                                                                             int(country_id),
                                                                                              int(region_id),
                                                                                              int(city_id), 
                                                                                              str(s_id), 
                                                                                              int(worker), 
                                                                                              int(is_closed), 
                                                                                              int(friends_count), 
                                                                                              int(members), 
                                                                                              str(resource_name), 
                                                                                              str(link), 
                                                                                              str(image_profile), 
                                                                                                stability, 
                                                                                                info_check)

        print(q)

        return db.q('imasv2', 'insert', q)



    def update_res_social(self, new_country_id,new_region_id,new_city_id, new_s_id, new_closed, new_friends_count, new_members_count, new_resource_name, new_link, new_image):
        db.q('imasv2', 'insert', """UPDATE resource_social 
               SET is_closed={0}, friends_count={1}, members={2}, resource_name='{3}', image_profile='{4}', info_check=1, country_id={5}, region_id={6}, city_id={7}
               WHERE type=2
               AND s_id = '{8}'""".format(new_closed, new_friends_count, new_members_count, new_resource_name, new_image, new_country_id,new_region_id,new_city_id, new_s_id))

        return db.q('imasv2', 'insert', """UPDATE resource_social
                                           SET is_closed={0}, friends_count={1}, members={2}, resource_name='{3}', link='{4}', image_profile='{5}', info_check=1, country_id={7}, region_id={8}, city_id={9}
                                           WHERE type=2
                                           AND s_id = '{6}'""".format(new_closed, new_friends_count, new_members_count, new_resource_name, new_link, new_image, new_s_id, new_country_id,new_region_id,new_city_id))



    def get_PofileIdPort(self,type_):
        return db.q_new('python_rest', 'select', """SELECT sessionid,port,name,proxy_type,priority
                                                    FROM soc_accounts
                                                    WHERE type = '{0}'""".format(type_))

    def get_GoToken(self):
        return db.q_new('python_rest', 'select', """SELECT sessionid
                                                    FROM soc_accounts
                                                    WHERE type = 'GoLogin2'
                                                     ORDER BY use_date DESC LIMIT 1""")[0][0]
    
