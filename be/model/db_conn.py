from be.model import store
from be.model.store import getDatabaseSession
from be.model.store import User_table, User_store, Store_table, New_order

class DBConn:
    def __init__(self):
        self.conn = getDatabaseSession ()
        #self.mongo = store.get_db_mongo()

    def user_id_exist(self, user_id):
        #cursor = self.conn.execute("SELECT user_id FROM user WHERE user_id = ?;", (user_id,))
        #row = cursor.fetchone()
        result = self.conn.query(User_table).filter(User_table.user_id == user_id).all()
        if len(result) == 0:
            return False
        else:
            return True

    def book_id_exist(self, store_id, book_id):
        #cursor = self.conn.execute("SELECT book_id FROM store WHERE store_id = ? AND book_id = ?;", (store_id, book_id))
        #row = cursor.fetchone()
        result = self.conn.query(Store_table).filter(Store_table.store_id == store_id, Store_table.book_id == book_id).all()
        if len(result) == 0:
            return False
        else:
            return True

    def store_id_exist(self, store_id):
        #cursor = self.conn.execute("SELECT store_id FROM user_store WHERE store_id = ?;", (store_id,))
        #row = cursor.fetchone()
        result = self.conn.query(User_store).filter(User_store.store_id == store_id).all()
        if len(result) == 0:
            return False
        else:
            return True

    def order_id_exist(self, order_id):
        #cursor = self.conn.execute("SELECT order_id FROM new_order WHERE order_id = ?;", (order_id,))
        #row = cursor.fetchone()
        result = self.conn.query(New_order).filter(New_order.order_id == order_id).all()
        if len(result) == 0:
            return False
        else:
            return True