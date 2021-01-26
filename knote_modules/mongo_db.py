import pymongo

mongo_srv = "mongodb+srv://me:DsqKPNqbhgEg4mNW@mycluster.uiznh.gcp.mongodb.net/sample_mflix?retryWrites=true&w=majority"

class DBmongo:
    def __init__(self, addr):
        self.db_path = addr
        self.conn = pymongo.MongoClient(self.db_path)
    #   self.db = self.conn['jim_db']
    #    self.create_chat_table()       #  Create automatically
    #    self.create_users_table()      #  Create automatically

    def create_chat_table(self):
        query = "db.createCollection('mainchat')"
        self.db.execute(query)

    def create_users_table(self):
        query = "db.createCollection('users')"
        self.db.execute(query)

    def add_mainchat_message(self, user: str, msg: str):
        coll = self.db['mainchat']
        dt = datetime.now().strftime('%b %d %Y %I:%M%p')
        q = {"date": dt, "user": user, "msg": msg}
        coll.insert_one(q)

    # def add_user(self, user: str, status: str):
    #     coll = self.db['users']
    #     dt = datetime.now().strftime('%b %d %Y %I:%M%p')
    #     q = {"date": dt, "user": user, "status": status}
    #     coll.insert_one(q)

    def end(self):
        return self.conn.close()

mon = DBmongo(mongo_srv)