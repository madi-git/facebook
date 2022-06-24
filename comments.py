from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import func
from apiclient.discovery import build
from apiclient.errors import HttpError

from celery import Celery
from celery import chord
from celery.signals import (worker_process_init, task_failure,
                            worker_process_shutdown, worker_ready)

from configs import base as config, celeryconfigs
from configs.base import VK_TOKEN

from datetime import datetime
from database.connection import engine_base, engine_temp, engine_comment
from database.models import (Post, Resource, OkAnchors, LoggingTasks, CommentTask,
                             SocAnalyzerItems, SocSectionItems,
                             FolderPrivilages)



from utils.users import (get_users_vk_util, get_users_fb_util)
from utils.comments import (get_commets_vk_wall, get_commets_fb_wall,
                            get_commets_twitter_wall)


from sqlalchemy.exc import SQLAlchemyError
import dateutil.parser as dateparser
from dateutil.parser import parse



import re
import os

import facebook
import vk
import tweepy

import emails
import logging
import random
import requests
import json
import traceback
import pymysql
import time


    

app = Celery('comments')
logging.basicConfig(
    format=u'%(levelname)-8s [%(asctime)s] %(message)s',
    level=logging.ERROR,
    filename=u'logging_social_tasks_comments.log')

app.config_from_object(celeryconfigs)

db_base = None
db_temp = None
db_comment = None
graph = None
requests_session = None
twitter_api = None
api_ok = None
api_my_mail = None
fb_token = 0
vk_api_session = []


def connection_base():
    global db_base
    if not db_base:
        db_base = scoped_session(
            sessionmaker(
                autocommit=False, autoflush=False, bind=engine_base))
    return db_base

def connection_temp():
    global db_temp
    if not db_temp:
        db_temp = scoped_session(
            sessionmaker(
                autocommit=False, autoflush=False, bind=engine_temp))
    return db_temp

def connection_comment():
    global db_comment
    if not db_comment:
        db_comment = scoped_session(
            sessionmaker(
                autocommit=False, autoflush=False, bind=engine_comment))
    return db_comment

def filter_utf8_string(string):
    re_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    return re_pattern.sub(u'\uFFFD', string)


def random_vk_session():
    return random.randint(0, len(VK_TOKEN) - 1)


def set_fb_token(e):
    global graph
    global fb_token
    try:
        graph = facebook.GraphAPI(config.FACEBOOK_ACCESS_TOKEN[fb_token + 1])
    except:
        fb_token = 0
        graph = facebook.GraphAPI(config.FACEBOOK_ACCESS_TOKEN[fb_token])
    return True



@worker_ready.connect
def worker_ready(signal=None, **kwargs):
    print("I am ready")


@worker_process_init.connect
def init_worker(signal=None, **kwargs):
    global graph
    global requests_session
    global twitter_api
    global db_comment
    global api_ok
    global api_my_mail

    print('Initializing database connection for worker.')
    db_comment = connection_comment()
    graph = facebook.GraphAPI(config.FACEBOOK_ACCESS_TOKEN[0])
    requests_session = requests.Session()

    auth = tweepy.OAuthHandler(config.TWITTER_CUNSUMER_KEY[2],
                               config.TWITTER_CUNSUMER_KEY_SECRET[2])
    auth.set_access_token(config.TWITTER_ACCESS_TOKEN[2],
                          config.TWITTER_ACCESS_TOKEN_SECRET[2])

    twitter_api = tweepy.API(auth)



    for vk_token in VK_TOKEN:
        session = vk.Session(access_token=vk_token)
        api = vk.API(session, v='5.52', lang='ru')
        vk_api_session.append(api)


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    if db_comment:
        print('Closing database connectionn for worker.')
        db_comment.close()


@task_failure.connect
def failure(exception=None, args=None, einfo=None):
    global db_comment
    db_comment = connection_comment()
    log = LoggingTasks(
        args.get('source_id', 0), ','.join(args), str(exception), str(einfo))
    db_temp.add(log)
    db_temp.commit()
    return True

   
        

#**************************************************************Парсер ВК-юзеров
@app.task(rate_limit="2/s", routing_key="user_comm_vk_1", queue="user_comm_vk_1")
def get_users_vk_1(user_ids, queue='user_comm_vk_1'):
    global db_comment
    db_comment = connection_comment()

    try:
        api = vk_api_session[random_vk_session()]
        users = api.users.get(
            user_ids=",".join(user_ids),
            fields='bdate,city,country,photo_100,screen_name,sex')
        get_users_vk_util(users, db_comment)
    except:
        get_users_vk_1.apply_async(args=(user_ids, queue), queue=queue)
        return False

    return True


#**************************************************************Парсер ВК-комментариев
@app.task(rate_limit="2/s", routing_key="comment_vk_1", queue="comment_vk_1")
def get_comments_vk_1(owner_id,
                    post_id,
                    last_post,
                    status_id,
                    queue="comment_vk_1",
                    old=0,
                    start_comment_id=None,
                    ):
    global db_comment
    db_comment = connection_comment()

    comment_count = 0
    comments = None

    if post_id == last_post:
        print("last_post_yes")
        comment_success.apply_async(args=(status_id,))



    else:
        print("No!")
    print(last_post)    

    try:
        api = vk_api_session[random_vk_session()]
        comments = api.wall.getComments(
            owner_id=owner_id,
            post_id=post_id,
            start_comment_id=start_comment_id,
            count=100,
            extended=1)
    except:
        get_comments_vk_1.apply_async(
            args=(owner_id, post_id, queue, old, start_comment_id),
            queue=queue)
        return False

    if comments:
        comment_count = get_commets_vk_wall(comments['items'], owner_id,
                                            post_id, db_comment)
        print("comments['items']_vk", comments['items'])
        user_ids = [str(user['id']) for user in comments['profiles']]
        print("user_ids_vk", user_ids)
        get_users_vk_1.apply_async(
            args=(user_ids, 'user_comm_vk_1'), queue='user_comm_vk_1')
        if comment_count in (100, 99):
            get_comments_vk_1.apply_async(
                args=(owner_id, post_id, queue, old,
                      comments['items'][-1]['id']),
                queue=queue)
        return True
    return False


#**************************************************************Парсер ВК-юзеров
@app.task(rate_limit="2/s", routing_key="user_comm_vk_2", queue="user_comm_vk_2")
def get_users_vk_2(user_ids, queue='user_comm_vk_2'):
    global db_comment
    db_comment = connection_comment()

    try:
        api = vk_api_session[random_vk_session()]
        users = api.users.get(
            user_ids=",".join(user_ids),
            fields='bdate,city,country,photo_100,screen_name,sex')
        get_users_vk_util(users, db_comment)
    except:
        get_users_vk_2.apply_async(args=(user_ids, queue), queue=queue)
        return False

    return True


#**************************************************************Парсер ВК-комментариев
@app.task(rate_limit="2/s", routing_key="comment_vk_2", queue="comment_vk_2")
def get_comments_vk_2(owner_id,
                    post_id,
                    last_post,
                    status_id,
                    queue="comment_vk_2",
                    old=0,
                    start_comment_id=None,
                    ):
    global db_comment
    db_comment = connection_comment()
    comment_count = 0
    comments = None

    if post_id == last_post:
        print("last_post_yes")
        callback2 = comment_success.apply_async(args=(status_id,))




    else:
        print("No!")
    print(last_post)    

    try:
        api = vk_api_session[random_vk_session()]
        comments = api.wall.getComments(
            owner_id=owner_id,
            post_id=post_id,
            start_comment_id=start_comment_id,
            count=100,
            extended=1)
    except:
        get_comments_vk_2.apply_async(
            args=(owner_id, post_id, queue, old, start_comment_id),
            queue=queue)
        return False

    if comments:
        comment_count = get_commets_vk_wall(comments['items'], owner_id,
                                            post_id, db_comment)
        user_ids = [str(user['id']) for user in comments['profiles']]
        get_users_vk_2.apply_async(
            args=(user_ids, 'user_comm_vk_2'), queue='user_comm_vk_2')
        if comment_count in (100, 99):
            get_comments_vk_2.apply_async(
                args=(owner_id, post_id, queue, old,
                      comments['items'][-1]['id']),
                queue=queue)
        return True
    return False

#**************************************************************Парсер ВК-юзеров
@app.task(rate_limit="2/s", routing_key="user_comm_vk_3", queue="user_comm_vk_3")
def get_users_vk_3(user_ids, queue='user_comm_vk_3'):
    global db_comment
    db_comment = connection_comment()

    try:
        api = vk_api_session[random_vk_session()]
        users = api.users.get(
            user_ids=",".join(user_ids),
            fields='bdate,city,country,photo_100,screen_name,sex')
        get_users_vk_util(users, db_comment)
    except:
        get_users_vk_3.apply_async(args=(user_ids, queue), queue=queue)
        return False

    return True


#**************************************************************Парсер ВК-комментариев
@app.task(rate_limit="2/s", routing_key="comment_vk_3", queue="comment_vk_3")
def get_comments_vk_3(owner_id,
                    post_id,
                    last_post,
                    status_id,
                    queue="comment_vk_3",
                    old=0,
                    start_comment_id=None,
                    ):
    global db_comment
    db_comment = connection_comment()
    comment_count = 0
    comments = None

    if post_id == last_post:
        print("last_post_yes")
        callback2 = comment_success.apply_async(args=(status_id,))




    else:
        print("No!")
    print(last_post)    

    try:
        api = vk_api_session[random_vk_session()]
        comments = api.wall.getComments(
            owner_id=owner_id,
            post_id=post_id,
            start_comment_id=start_comment_id,
            count=100,
            extended=1)
    except:
        get_comments_vk_3.apply_async(
            args=(owner_id, post_id, queue, old, start_comment_id),
            queue=queue)
        return False

    if comments:
        comment_count = get_commets_vk_wall(comments['items'], owner_id,
                                            post_id, db_comment)
        user_ids = [str(user['id']) for user in comments['profiles']]
        get_users_vk_3.apply_async(
            args=(user_ids, 'user_comm_vk_3'), queue='user_comm_vk_3')
        if comment_count in (100, 99):
            get_comments_vk_3.apply_async(
                args=(owner_id, post_id, queue, old,
                      comments['items'][-1]['id']),
                queue=queue)
        return True
    return False


@app.task(rate_limit="50/m", routing_key="comment_fb_2", queue="comment_fb_2")
def get_comments_fb_2(owner_id,
                    post_id,
                    last_post,
                    status_id,
                    queue="comment_fb_2",
                    old=0,
                    start_comment_id=None):
    global graph
    global set_fb_token
    comments = {}
    global db_comment
    db_comment = connection_comment()

    try:
        args = {
            'fields': 'id,from,created_time,message,source,attachment',
            'order': 'reverse_chronological',
            'filter': 'stream',
            'limit': '50',
            'after': start_comment_id
        }
        
        if post_id == last_post:
            print("last_post_yes")
            callback3 = comment_success.apply_async(args=(status_id,))

        else:
            print("No!")
            print(last_post)

        comments = graph.get_connections(
            id='%s_%s' % (owner_id, post_id),
            connection_name='comments',
            **args)
        get_commets_fb_wall(comments['data'], owner_id, post_id, db_comment)
        user_ids = [comment['from']['id'] for comment in comments['data']]
        get_user_fb_2.apply_async(
            args=(user_ids, "user_comm_fb_2"), queue="user_comm_fb_2")
    except facebook.GraphAPIError as e:
        get_comments_fb_2.apply_async(
            args=(owner_id, post_id, queue, old, start_comment_id),
            queue=queue)
        if int(e.code) == 17:
            set_fb_token(e)
        return False
    except Exception as e:
        print(e)

    if 'next' in comments.get('paging', {}):
        after = comments['paging']['cursors']['after']
        get_comments_fb_2.apply_async(
            args=(owner_id, post_id, queue, 1, after), queue=queue)
        if old == 0:
            pass  # get_comments_fb.apply_async(args=(owner_id, post_id, queue, 0, None), queue=queue)
    return True

@app.task(rate_limit="100/m", routing_key="user_comm_fb_2", queue="user_comm_fb_2")
def get_user_fb_2(user_ids, queue="user_comm_fb_2"):
    global graph
    global fb_token
    global db_comment
    db_comment = connection_comment()

    try:
        args = {
            'fields':
            'id,birthday,gender,first_name,last_name,location,picture.type(large)'
        }
        users = graph.get_objects(ids=user_ids, **args)
        get_users_fb_util(users, db_comment)
    except facebook.GraphAPIError as e:
        get_user_fb_2.apply_async(args=(user_ids, queue), queue=queue)
        if int(e.code) == 17:
            set_fb_token(e)
        return False
    except Exception as e:
        get_user_fb_2.apply_async(args=(user_ids, queue), queue=queue)
        return False
    return True

@app.task(rate_limit="50/m", routing_key="comment_fb_3", queue="comment_fb_3")
def get_comments_fb_3(owner_id,
                    post_id,
                    last_post,
                    status_id,
                    queue="comment_fb_3",
                    old=0,
                    start_comment_id=None):
    global graph
    global set_fb_token
    global db_comment
    comments = {}
    db_comment = connection_comment()
    try:
        args = {
            'fields': 'id,from,created_time,message,source,attachment',
            'order': 'reverse_chronological',
            'filter': 'stream',
            'limit': '50',
            'after': start_comment_id
        }
        
        if post_id == last_post:
            print("last_post_yes")
            callback3 = comment_success.apply_async(args=(status_id,))

        else:
            print("No!")
            print(last_post)

        comments = graph.get_connections(
            id='%s_%s' % (owner_id, post_id),
            connection_name='comments',
            **args)
        get_commets_fb_wall(comments['data'], owner_id, post_id, db_comment)
        user_ids = [comment['from']['id'] for comment in comments['data']]
        get_user_fb_3.apply_async(
            args=(user_ids, "user_comm_fb_3"), queue="user_comm_fb_3")
    except facebook.GraphAPIError as e:
        get_comments_fb_3.apply_async(
            args=(owner_id, post_id, queue, old, start_comment_id),
            queue=queue)
        if int(e.code) == 17:
            set_fb_token(e)
        return False
    except Exception as e:
        print(e)

    if 'next' in comments.get('paging', {}):
        after = comments['paging']['cursors']['after']
        get_comments_fb_3.apply_async(
            args=(owner_id, post_id, queue, 1, after), queue=queue)
        if old == 0:
            pass  # get_comments_fb.apply_async(args=(owner_id, post_id, queue, 0, None), queue=queue)
    return True


@app.task(rate_limit="100/m", routing_key="user_comm_fb_3", queue="user_comm_fb_3")
def get_user_fb_3(user_ids, queue="user_comm_fb_3"):
    global db_comment
    global graph
    global fb_token
    db_comment = connection_comment()

    try:
        args = {
            'fields':
            'id,birthday,gender,first_name,last_name,location,picture.type(large)'
        }
        users = graph.get_objects(ids=user_ids, **args)
        get_users_fb_util(users, db_comment)
    except facebook.GraphAPIError as e:
        get_user_fb_3.apply_async(args=(user_ids, queue), queue=queue)
        if int(e.code) == 17:
            set_fb_token(e)
        return False
    except Exception as e:
        get_user_fb_3.apply_async(args=(user_ids, queue), queue=queue)
        return False
    return True



@app.task(rate_limit="50/m", routing_key="comment_fb_1", queue="comment_fb_1")
def get_comments_fb_1(owner_id,
                    post_id,
                    last_post,
                    status_id,
                    queue="comment_fb_1",
                    old=0,
                    start_comment_id=None):
    global graph
    global set_fb_token
    comments = {}
    global db_comment
    db_comment = connection_comment()
    try:
        args = {
            'fields': 'id,from,created_time,message,source,attachment',
            'order': 'reverse_chronological',
            'filter': 'stream',
            'limit': '50',
            'after': start_comment_id
        }
        
       

        comments = graph.get_connections(
            id='%s_%s' % (owner_id, post_id),
            connection_name='comments',
            **args)
        print("comments['data']", comments['data'])
        get_commets_fb_wall(comments['data'], owner_id, post_id, db_comment)
        user_ids = [comment['from']['id'] for comment in comments['data']]
        print("user_ids", user_ids)
        get_user_fb_1.apply_async(
            args=(user_ids, "user_comm_fb_1"), queue="user_comm_fb_1")

        if post_id == last_post:
            print("last_post_yes")
            callback3 = comment_success.apply_async(args=(status_id,))

        else:
            print("No!")
            print(last_post)
    except facebook.GraphAPIError as e:
        get_comments_fb_1.apply_async(
            args=(owner_id, post_id, queue, old, start_comment_id),
            queue=queue)
        if int(e.code) == 17:
            set_fb_token(e)
        return False
    except Exception as e:
        print(e)

    if 'next' in comments.get('paging', {}):
        after = comments['paging']['cursors']['after']
        get_comments_fb_1.apply_async(
            args=(owner_id, post_id, queue, 1, after), queue=queue)
        if old == 0:
            pass  # get_comments_fb.apply_async(args=(owner_id, post_id, queue, 0, None), queue=queue)
    return True

@app.task(rate_limit="100/m", routing_key="user_comm_fb_1", queue="user_comm_fb_1")
def get_user_fb_1(user_ids, queue="user_comm_fb_1"):
    global graph
    global fb_token
    global db_comment
    db_comment = connection_comment()

    try:
        args = {
            'fields':
            'id,birthday,gender,first_name,last_name,location,picture.type(large)'
        }
        users = graph.get_objects(ids=user_ids, **args)
        get_users_fb_util(users, db_comment)
    except facebook.GraphAPIError as e:
        print(e)
        # get_user_fb_1.apply_async(args=(user_ids, queue), queue=queue)
        # if int(e.code) == 17:
        #     set_fb_token(e)
        return False
    except Exception as e:
        print(e)
        # get_user_fb_1.apply_async(args=(user_ids, queue), queue=queue)
        return False
    return True




#**************************************************************Парсер Твиттер-комментариев
@app.task(rate_limit="20/m", routing_key="comment_twitter", queue="comment_twitter")
def get_comments_twitter(screen_name, post_id, status_id, queue="comment_twitter"):
    global db_comment
    global twitter_api
    # db_comment = connection_comment()
    # post_id=int(post_id)
    # screen_name = str(screen_name)

    try:
        print("Yea", screen_name)
        time.sleep(10)
        data= tweepy.Cursor(twitter_api.search,
                           q=screen_name.strip(' \t\n\r'),
                           include_entities='true',
                           rpp=3, count=100,
                           since_id=post_id)
        print(screen_name, post_id)
        print("dataaaa", data)
        get_commets_twitter_wall(data, screen_name, post_id, db_comment)

        
    except Exception as e:
        print("twitter_comments", e)
        # get_comments_twitter.apply_async(
        #     args=(screen_name, post_id, queue), queue=queue)
        return False
    # callback5 = comment_success.apply_async(args=(status_id,))

    return True


#**************************************************************Функция завершения отработки
@app.task(routing_key="comment_status", queue="comment_status")
def comment_success(status_id, result=None):
    try:
        global db_comment
        db_comment = connection_comment()
        db_comment.query(CommentTask).filter_by(id=status_id).update({
            'status': 'success',
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        db_comment.commit()
        return True
    except Exception as e:
        print(e)



#****************************************************************Выборка задач для отработки
@app.task(routing_key="comment_start", queue="comment_start")
def set_comment_start(a_id=None, f_id=None, s_id=None, p_id=None, status_id=None, result=None):
    
    type_social = (1, 2, 3)
    tasks = []
    global db_comment
    db_comment = connection_comment()

    if a_id:
        posts = db_comment.query(Post.owner_id,
                         Post.item_id,
                         Resource.screen_name,
                         Resource.type,
                         Resource.link) \
                  .filter(SocAnalyzerItems.analyzer_id==a_id,
                          Post.id==SocAnalyzerItems.item_id,
                          Resource.id==Post.res_id,
                          Resource.type.in_(type_social)) \
                .all()

    elif f_id:
        posts = db_comment.query(Post.owner_id,
                         Post.item_id,
                         Resource.screen_name,
                         Resource.type,
                         Resource.link) \
                  .filter(FolderPrivilages.f_id==f_id,
                          Post.id==FolderPrivilages.news_id,
                          Resource.id==Post.res_id,
                          Resource.type.in_(type_social)) \
                  .all()


    elif s_id:
        posts = db_comment.query(Post.owner_id,
                         Post.item_id,
                         Resource.screen_name,
                         Resource.type,
                         Resource.link) \
                  .filter(SocSectionItems.section_id==s_id,
                          Post.id==SocSectionItems.item_id,
                          Resource.id==Post.res_id,
                          Resource.type.in_(type_social)) \
                  .all()

    else:
        return False


    if p_id == 1:
        try:
            for post in posts:
                print("type", post.type)
                if int(post.type) == int(1):
                    tasks.append(get_comments_vk_1.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(2):
                    tasks.append(get_comments_fb_1.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(3):
                #     # try:
                    link = str(post.link).strip(' \t\n\r')
                    print("link_twitter",link)
                    screen_name = link.split('com/')[1].replace('\'','')

                    # print("link", link)
                    print("screen_name", screen_name)
                    tasks.append(get_comments_twitter.subtask((screen_name, post[1], status_id)))
                        # else:
                        #     print("no link")
                    # except Exception as e:
                    #     print("twit", e)
                else:
                    print("No type")
        except Exception as e:
            print("set_comments1", e)


    elif p_id == 2:
        try:
            for post in posts:
                print("type", post.type)
                if int(post.type) == int(1):
                    tasks.append(get_comments_vk_2.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(2):
                    tasks.append(get_comments_fb_2.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(3):
                #     # try:
                    link = str(post.link).strip(' \t\n\r')
                    print("link_twitter",link)
                    screen_name = link.split('com/')[1].replace('\'','')

                    # print("link", link)
                    print("screen_name", screen_name)
                    tasks.append(get_comments_twitter.subtask((screen_name, post[1], status_id)))
                        # else:
                        #     print("no link")
                    # except Exception as e:
                    #     print("twit", e)
                else:
                    print("No type")
        except Exception as e:
            print("set_comments2", e)

    elif p_id == 3:
        try:
            for post in posts:
                print("type", post.type)
                if int(post.type) == int(1):
                    tasks.append(get_comments_vk_3.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(2):
                    tasks.append(get_comments_fb_3.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(3):
                #     # try:
                    link = str(post.link).strip(' \t\n\r')
                    print("link_twitter",link)
                    screen_name = link.split('com/')[1].replace('\'','')

                    # print("link", link)
                    print("screen_name", screen_name)
                    tasks.append(get_comments_twitter.subtask((screen_name, post[1], status_id)))
                        # else:
                        #     print("no link")
                    # except Exception as e:
                    #     print("twit", e)
                else:
                    print("No type")
        except Exception as e:
            print("set_comments3", e)
    


    elif p_id == None:
        try:
            for post in posts:
                print("type", post.type)
                if int(post.type) == int(1):
                    tasks.append(get_comments_vk_1.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(2):
                    tasks.append(get_comments_fb_1.subtask((post[0], post[1], \
                                                            last_post[1], status_id)))
                elif int(post.type) == int(3):
                #     # try:
                    link = str(post.link).strip(' \t\n\r')
                    print("link_twitter",link)
                    screen_name = link.split('com/')[1].replace('\'','')

                    # print("link", link)
                    print("screen_name", screen_name)
                    tasks.append(get_comments_twitter.subtask((screen_name, post[1], status_id)))
                        # else:
                        #     print("no link")
                    # except Exception as e:
                    #     print("twit", e)
                else:
                    print("No type")
        except Exception as e:
            print("set_comments4", e)

    else:
        pass


           # elif post.type == 3:
           #     if post.screen_name:
           #         screen_name = post.screen_name.strip(' \t\n\r')
           #         tasks.append(get_comments_twitter.subtask((screen_name, post[1])))
    try:
        callback1 = comment_success.subtask((status_id,))
        chord(tasks)(callback1)
        return True
    except Exception as e:
        print("success", e)
        return False
    return True
