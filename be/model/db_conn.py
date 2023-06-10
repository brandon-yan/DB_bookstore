from be.model import store
from be.model.store import getDatabaseSession
from be.model.store import User_table, User_store, Store_table, New_order

class DBConn:
    def __init__(self):
        self.conn = getDatabaseSession ()
        #self.mongo = store.get_db_mongo()

    def user_id_exist(self, user_id):
        result = self.conn.query(User_table).filter(User_table.user_id == user_id).all()
        if len(result) == 0:
            return False
        else:
            return True

    def book_id_exist(self, store_id, book_id):
        result = self.conn.query(Store_table).filter(Store_table.store_id == store_id, Store_table.book_id == book_id).all()
        if len(result) == 0:
            return False
        else:
            return True

    def store_id_exist(self, store_id):
        result = self.conn.query(User_store).filter(User_store.store_id == store_id).all()
        if len(result) == 0:
            return False
        else:
            return True

    def order_id_exist(self, order_id):
        result = self.conn.query(New_order).filter(New_order.order_id == order_id).all()
        if len(result) == 0:
            return False
        else:
            return True