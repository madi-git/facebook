import pymysql

# CONNECTS
db_base_ = 'x'
db_base = 'x'
db_rest = 'x'
# user_base = 'x'
host_base = 'x'
# host_base = 'x'
# password_base = 'x'
user_base="x"
password_base = "x"

# QUERY
class DB:
    def q_new(self, base, type, query, many=0, data=''):
        try:

            conn = pymysql.connect(host='x',
                                   user='x',
                                   password='x',
                                   db='x',
                                   charset='x',
                                   autocommit=True)
            cur = conn.cursor()
            if many == 0:
                cur.execute(query)
            if many == 1:
                cur.executemany(query, data)

            if type == 'select':
                resources = cur.fetchall()
                return resources
        except Exception as e:
            print("qError", e)
        finally:
            cur.close()
            conn.close()

    def q_new_last_id(self, base, type, query, many=0, data=''):
        try:

            conn = pymysql.connect(host='x',
                                   user='x',
                                   password='x',
                                   db='x',
                                   charset='utf8',
                                   autocommit=True)
            cur = conn.cursor()
            cur.execute(query)
            return cur.lastrowid
        except Exception as e:
            print("qError", e)
        finally:
            cur.close()
            conn.close()



    def q(self, base, type, query, many=0, data=''):
        try:
            if base == 'x':
                db_name = db_base
            if base == 'x':
                db_name = db_base_
            elif base == 'x':
                db_name = db_rest
            else:
                db_name = db_base
            conn = pymysql.connect(host=host_base,
                                   user=user_base,
                                   password=password_base,
                                   db=db_name,
                                   charset='utf8',
                                   autocommit=True)
            cur = conn.cursor()
            if many == 0:
                cur.execute(query)
            if many == 1:
                cur.executemany(query, data)

            if type == 'select':
                resources = cur.fetchall()
                return resources
        except Exception as e:
            print("qError", e)
        finally:
            cur.close()
            conn.close()


    def q2(self, base, type, query, many=0, data=''):
        try:
            if base == 'x':
                db_name = db_base
            if base == 'x':
                db_name = db_base_
            elif base == 'x':
                db_name = db_rest
            else:
                db_name = db_base
            conn = pymysql.connect(host='x',
                                   user=user_base,
                                   password=password_base,
                                   db=db_name,
                                   charset='utf8',
                                   autocommit=True)
            cur = conn.cursor()
            if many == 0:
                cur.execute(query)
            if many == 1:
                cur.executemany(query, data)

            if type == 'select':
                resources = cur.fetchall()
                return resources
        except Exception as e:
            print("qError", e)
        finally:
            cur.close()
            conn.close()

