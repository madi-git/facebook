#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from connects2 import DB as Db2
from connects1 import DB as Db1
from datetime import datetime
from bs4 import BeautifulSoup
import pymysql
import json
import dateparser
import time
import random

db1 = Db1()
db2 = Db2()

# QUERY
class Metrics():
    print('start') 
    ####GET TOKENSs
    def get_metrics(self, full_link, driver, item_id):
        likes_count = 0
        repost_count = 0
        comments_count = 0
        
        # r = requests.Session()
        
        full_link = full_link.replace("/facebook", '/www.facebook')
        full_link = full_link.replace("_", "/posts/")
        
        driver.get(full_link)
        time.sleep(random.randint(10,15))
        status_code = 200

        driver.save_screenshot("/home/fb_metrics/post.png")
        if status_code == 200:
            data = str(driver.page_source)
            
            def get_data(end_):
                try:
                    full = start + str(p).split(end_)[0]
                    data_ = json.loads(full)
                    for i in data_['require']:
                        for x in i:
                            if "i18n_reaction_count" in str(x):
                                for b in x:
                                    if "i18n_reaction_count" in str(b):
                                        try:
                                            f = b['__bbox']['result']['data']
                                            # print(f)

                                            clss_ =['node', 'nodes']
                                            for clss in clss_:
                                                try:
                                                    n = f[clss]
                                                    #print(n)
                                                    if type(n) == list:
                                                        counts = n[0]['comet_sections']['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']
                                                        
                                                        repost_count = counts['share_count']['count']
                                                        likes_count = counts['reaction_count']['count']
                                                        comments_count = counts['comments_count_summary_renderer']['feedback']['i18n_comment_count']
                                                    if type(n) != list:
                                                        counts = n['comet_sections']['feedback']['story']['feedback_context']['feedback_target_with_context']['ufi_renderer']['feedback']['comet_ufi_summary_and_actions_renderer']['feedback']
                                                        
                                                        repost_count = counts['share_count']['count']
                                                        likes_count = counts['reaction_count']['count']
                                                        comments_count = counts['comments_count_summary_renderer']['feedback']['i18n_comment_count']

                                                    print("reposts", repost_count)
                                                    print("comments", comments_count)
                                                    print("like", likes_count)
                                                except:
                                                    pass
                                        except:
                                            pass
                except:
                    pass

                return (repost_count,comments_count, likes_count)



            classes =['define', 'require']
            for class_ in classes:
                for p in str(data).split("{(new ServerJS()).handleWithCustomApplyEach(ScheduledApplyEach,{\"%s\":"%(class_)):
                    try:
                        # if "DateFormatConfig" in p:
                        try:
                            start = "{\"%s\":"%(class_)
                            ends_ =[");});});}})});</script>", ");});});</script>"]

                            for end_ in ends_:
                                try:
                                    metrics_data = get_data(end_)

                                    repost_count = metrics_data[0]
                                    comments_count = metrics_data[1] 
                                    likes_count = metrics_data[2] 
                                except:
                                    pass
                        except:
                            pass

                            # print("------", full)
                    except:
                        pass

        return (status_code, likes_count, repost_count, comments_count)
        
    
    def get_proxies(self):
        return db2.q_new('python_rest', 'select', """SELECT
                    CONCAT("https://",login,":",password,"@",proxy,":", port)
                    FROM  proxies
                    WHERE type = 'dynamic' AND script = 'fb_inst_metrics'""")
    
    def start_stream(self, ids):
        db2.q_new("python_rest", 'update', """UPDATE metrics_manual_posts
                                         SET s_date=NOW()
                                         WHERE post_id IN ({0}) """.format(ids))
    
    def get_posts(self, stream):
        ids = []
        data = []

        manual_ids = db2.q_new('python_rest', 'select', """SELECT id, post_id
                                                        FROM metrics_manual_posts
                                                        WHERE type = 2
                                                        -- AND post_id =818011150
                                                        AND status NOT IN (200,404,500)
                                                        AND f_date = '0000-00-00 00:00:00'
                                                        AND add_date > DATE_SUB(NOW(), INTERVAL 2 DAY)
                                                        ORDER BY add_date asc LIMIT 10""")

        for u in manual_ids:
            task_id = u[0]
            post_id = u[1]

            ids.append(post_id)


            try:
                print("post_id", post_id)

                link = db2.QueryClickHouse("""SELECT link FROM posts  WHERE id = {0} AND type=2""".format(post_id))[0][0]
                print("link", link)

                item_id = db2.QueryClickHouse("""SELECT item_id FROM posts_ids  WHERE id = {0}""".format(post_id))[0][0]
                print("item_id", item_id)


                    
                data.append((task_id,post_id, link, item_id))
            except Exception as e:
                self.update_finish_not(post_id)
                print("ClickError", e)
        return (ids, data)
    
    
    def update_finish(self, post_id, status_code):
        f_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db2.q_new("python_rest", 'update', """UPDATE metrics_manual_posts
        SET  f_date='{0}', status={1} WHERE post_id={2}""".format(f_date,
                                                                  status_code,
                                                                  post_id))
    
    def update_finish_200(self, ids):
        f_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db2.q_new("python_rest", 'update', """UPDATE metrics_manual_posts
                            SET  f_date='{0}', status=200
                            WHERE post_id IN ({1})""".format(f_date, ids))

    def update_finish_501(self, ids):
        f_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db2.q_new("python_rest", 'update', """UPDATE metrics_manual_posts
                                        SET  f_date='{0}', status=501
                                        WHERE post_id IN ({1})""".format(f_date, ids))  

    def update_finish_not(self, ids):
        f_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db2.q_new("python_rest", 'update', """UPDATE metrics_manual_posts
                                        SET  s_date='{0}', f_date='{0}', status=900
                                        WHERE post_id IN ({1})""".format(f_date, ids))
        
    
    def insert_metrics_all(self, data):
        db2.q_old("imas", 'update', """INSERT INTO posts_likes 
                                (`news_id`, `likes`, `comments`, `reposts`) 
                                VALUES (%s, %s, %s, %s) 
                                ON DUPLICATE KEY UPDATE likes=VALUES(likes), 
                                comments=VALUES(comments), 
                                reposts=VALUES(reposts)""", 1, data)




# QUERY
class Parsing():
    pass


class Queries():
    def getRepostAccount(self):
        return db1.q_new('python_rest', 'select', """SELECT login, password, id, sessionid
                                                FROM soc_accounts 
                                                WHERE type = 'FbMetrics1'
                                                LIMIT 1""")



    def UpdateUseDate(self, id_):
        db1.q_new("python_rest", 'update', """UPDATE soc_accounts
                                         SET use_date=NOW()
                                         WHERE id={0}""".format(id_))

    def getRepostProxy(self):
        return db1.q_new('python_rest', 'select', """SELECT CONCAT(proxy,":",port)
                                                FROM proxies WHERE type = 'static' 
                                                AND script LIKE '%servicefb%' 
                                                LIMIT 1""")[0][0]

    def getTasks(self):
        return db1.q('imasv2', 'select', """SELECT id,url,user_id,project_id FROM add_post 
                                           WHERE type=2 AND repost=1
                                           ORDER BY  priority DESC LIMIT 1""")

    def get_GoToken(self):
        return db1.q_new('python_rest', 'select', """SELECT sessionid
                                                    FROM soc_accounts
                                                    WHERE type='GoLogin'
                                                    ORDER BY use_date DESC LIMIT 1""")

    def get_PofileIdPort(self):
        return db1.q_new('python_rest', 'select', """SELECT profile_id,port,name,id
                                                    FROM soc_accounts
                                                    WHERE type = 'FbMetrics1'
                                                    ORDER BY use_date asc LIMIT 1""") #.format(type_))

    def updating(self, query):
        db1.q("imasv2", 'update', query)

