from sqlalchemy.exc import SQLAlchemyError
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from be.model.times import get_now_time, add_unpaid_order, delete_unpaid_order, check_order_time
from be.model.order import Order
from be.model.store import User_table, User_store, Store_table, New_order, New_order_detail, History_order, Invert_index
#from be.model.store import getDatabaseSession

class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)
        self.page_size = 20

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            total_price = 0
            for book_id, count in id_and_count:
                #cursor = self.conn.execute(
                #    "UPDATE new_store set stock_level = stock_level - ?"
                #    "WHERE store_id = ? and book_id = ? and stock_level >= ? "
                #    "RETURNING price", (count, store_id, book_id,count)
                #)
                row = session.query(Store_table).filter(
                    Store_table.store_id == store_id, Store_table.book_id == book_id, Store_table.stock_level >= count).all()
                if len(row) == 0:
                    session.rollback()
                    return error.error_stock_level_low(book_id) + (order_id,)
                session.query(Store_table).filter(
                    Store_table.store_id == store_id, Store_table.book_id == book_id,
                    Store_table.stock_level >= count).update(
                    {"stock_level": Store_table.stock_level - count})
                session.commit()
                #row = cursor.fetchone()
                price = row[0].price

                #self.conn.execute(
                #    "INSERT INTO new_order_detail(order_id, book_id, count) "
                #    "VALUES(?, ?, ?)",
                #    (uid, book_id, count)
                #)
                new_order_detail = New_order_detail(order_id=uid, book_id=book_id, count=count)
                session.add(new_order_detail)
                session.commit()
                total_price += count * price
            order_time = get_now_time()
            #self.conn.execute(
            #    "INSERT INTO new_order(order_id, store_id, user_id, total_price, order_time) "
            #    "VALUES(?, ?, ?, ?, ?)",
            #    (uid, store_id, user_id, total_price, order_time)
            #)
            new_order = New_order(order_id = uid, store_id = store_id, user_id = user_id, total_price = total_price, order_time = order_time, status = 1)
            session.add(new_order)
            session.commit()
            order_id = uid

            add_unpaid_order(order_id, order_time)
        except SQLAlchemyError as e:
            session.rollback()
            logging.info("528, {}".format(str(e)))
            print(str(e))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        session = self.conn
        try:
            #cursor = conn.execute("SELECT * FROM new_order WHERE order_id = ?", (order_id,))
            #row = cursor.fetchone()
            row = session.query(New_order).filter(New_order.order_id == order_id).all()
            if len(row) == 0:
                return error.error_invalid_order_id(order_id)

            order_id = row[0].order_id
            buyer_id = row[0].user_id
            store_id = row[0].store_id
            total_price = row[0].total_price
            order_time = row[0].order_time
            status = row[0].status

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if status != 1:
                return error.error_invalid_order_status()
            if not check_order_time(order_time):
                session.commit()
                delete_unpaid_order(order_id)
                o = Order()
                o.cancel_order(order_id)
                return error.error_invalid_order_id()

            #cursor = conn.execute("SELECT balance, password FROM user WHERE user_id = ?;", (buyer_id,))
            #row = cursor.fetchone()
            row =session.query(User_table).filter(User_table.user_id == buyer_id).all()
            if len(row) == 0:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0].balance
            if password != row[0].password:
                return error.error_authorization_fail()
            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)


            #cursor = conn.execute("UPDATE user set balance = balance - ?"
            #                      "WHERE user_id = ? AND balance >= ?",
            #                      (total_price, buyer_id, total_price))
            row = session.query(User_table).filter(User_table.user_id == buyer_id, User_table.balance >= total_price).update({"balance": User_table.balance - total_price})
            if row == 0:
                return error.error_not_sufficient_funds(order_id)
            session.commit()
            #self.conn.execute(
            #    "UPDATE new_order set status=2 where order_id = '%s' ;" % order_id)
            #self.conn.commit()
            session.query(New_order).filter(New_order.order_id == order_id).update({"status": 2})
            session.commit()
            delete_unpaid_order(order_id)
        except SQLAlchemyError as e:
            print(e)
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        session = self.conn
        try:
            #cursor = self.conn.execute("SELECT password  from user where user_id=?", (user_id,))
            #row = cursor.fetchone()
            row = session.query(User_table).filter(User_table.user_id == user_id).all()
            if len(row) == 0:
                return error.error_authorization_fail()

            if row[0].password != password:
                return error.error_authorization_fail()

            #cursor = self.conn.execute(
            #    "UPDATE user SET balance = balance + ? WHERE user_id = ?",
            #    (add_value, user_id))
            #if cursor.rowcount == 0:
            row = session.query(User_table).filter(User_table.user_id == user_id).all()
            if len(row) == 0:
                return error.error_non_exist_user_id(user_id)
            session.query(User_table).filter(User_table.user_id == user_id).update({"balance": User_table.balance + add_value})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e))

        return 200, "ok"

    def receive_books(self, user_id: str, password: str, order_id: str) -> (int, str):
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)

            #cursor = self.conn.execute(
            #    "SELECT order_id, user_id, store_id, total_price, status FROM new_order WHERE order_id = '%s';" % order_id
            #)
            #row = cursor.fetchone()
            row = session.query(New_order).filter(New_order.order_id == order_id).all()
            if len(row) == 0:
                return error.error_invalid_order_id(order_id)
            order_id = row[0].order_id
            buyer_id = row[0].user_id
            store_id = row[0].store_id
            total_price = row[0].total_price
            status = row[0].status

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if status != 3:
                return error.error_invalid_order_status(order_id)

            #cursor = self.conn.execute(
            #    "SELECT store_id, user_id FROM user_store WHERE store_id = '%s';" % store_id
            #)
            #row = cursor.fetchone()
            row = session.query(User_store).filter(User_store.store_id == store_id).all()
            if len(row) == 0:
                return error.error_non_exist_store_id(store_id)
            seller_id = row[0].user_id
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)
            #cursor = self.conn.execute(
            #    "UPDATE user set balance = balance + '%d' WHERE user_id = '%s';" %(total_price, seller_id)
            #)
            #if cursor.rowcount == 0:
            row = session.query(User_table).filter(User_table.user_id == seller_id).update({"balance": User_table.balance + total_price})
            if row == 0:
                return error.error_non_exist_user_id(buyer_id)

            session.commit()
            o = Order()
            o.cancel_order(order_id, end_status=4)

        except SQLAlchemyError as e:
            print(e)
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e))
        return 200, "ok"

    def cancel_order(self, buyer_id, order_id) -> (int, str):
        session = self.conn
        try:
            #cursor = self.conn.execute(
            #    "SELECT status FROM new_order WHERE order_id = '%s';" % order_id
            #)
            #row = cursor.fetchone()
            row = session.query(New_order).filter(New_order.order_id == order_id).all()
            if row[0].status != 1:
                return error.error_invalid_order_status(order_id)

            if not self.user_id_exist(buyer_id):
                return error.error_non_exist_user_id(buyer_id)
            if not self.order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)

            delete_unpaid_order(order_id)
            order = Order()
            order.cancel_order(order_id, end_status=0)
        except SQLAlchemyError as e:
            print(e)
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e))
        return 200, "ok"

    def query_new_order(self, user_id):
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                raise error.error_non_exist_user_id(user_id)

            result = []
            #cursor = self.conn.execute(
            #    "SELECT order_id, store_id, status, total_price, order_time FROM new_order WHERE user_id = '%s';" % user_id
            #)
            rows = session.query(New_order).filter(New_order.user_id == user_id).all()
            if len(rows) != 0:
                #rows = cursor.fetchall()
                for row in rows:
                    order = {
                        "order_id": row.order_id,
                        "store_id": row.store_id,
                        "status": row.status,
                        "total_price": row.total_price,
                        "order_time": row.order_time
                    }
                    books = []
                    #cursor = self.conn.execute(
                    #    "SELECT book_id, count FROM new_order_detail WHERE order_id = '%s'; " % order["order_id"]
                    #)
                    bookrows = session.query(New_order_detail).filter(New_order_detail.order_id == order["order_id"]).all()
                    #bookrows = cursor.fetchall()
                    for bookrow in bookrows:
                        book = {
                            "book_id": bookrow.book_id,
                            "count": bookrow.count
                        }
                        books.append(book)
                    order["books"] = books
                    result.append(order)
            else:
                result = ["NO Order is Processing"]
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e)), []
        #print(result)
        return 200, "ok", result

    def query_history_order(self, user_id):
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                raise error.error_non_exist_user_id(user_id)

            result = []
            #cursor = self.conn.execute(
            #    "SELECT order_id, store_id, status, total_price, order_time FROM history_order WHERE user_id = '%s';" % user_id
            #)
            rows = session.query(History_order).filter(History_order.user_id == user_id).all()
            if len(rows) != 0:
            #if cursor.rowcount != 0:
            #    rows = cursor.fetchall()
                for row in rows:
                    result.append(row)
            else:
                result = ["NO Order is Processing"]
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e)), []
        return 200, "ok", result

    # store_id: if not None, retrieve books stored in store_id
    def __find_one_key(self, key: str, store_id: str = None) -> (int, str, set):
        session = self.conn
        try:
            if store_id is None:
                #cursor = self.conn.execute(
                #    "SELECT book_id, book_title, book_author FROM invert_index WHERE search_key = '%s'; " % key
                #)
                rows = session.query(Invert_index).filter(Invert_index.search_key == key).all()
            else:
                #cursor = self.conn.execute(
                #    "SELECT book_id, book_title, book_author FROM invert_index WHERE search_key = '%s' and store_id = '%s'; " % (key, store_id)
                #)
                rows = session.query(Invert_index).filter(Invert_index.search_key == key, Invert_index.store_id == store_id).all()
            #rows = cursor.fetchall()
            book_ids = []
            for row in rows:
                book_ids.append(row.book_id)
            self.conn.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e)), set()

        return 200, "ok", set(book_ids)

    def __find_book_ids(self, keys: list, sep: bool, page: int, store_id: str = None) -> (int, str, list):
        session = self.conn
        try:
            book_ids = set()
            for key in keys:
                code, _, upds = self.__find_one_key(key, store_id)
                if code == 200:
                    book_ids.update(upds)
            book_ids = list(sorted(book_ids))
            if sep:
                off = page * self.page_size
                if off >= len(book_ids):
                    book_ids = []
                else:
                    book_ids = book_ids[off:min(len(book_ids), off + self.page_size)]
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e)), []

        return 200, "ok", book_ids

    def find(self, keys: list, sep: bool, page: int) -> (int, str, list):
        session = self.conn
        try:
            code, msg, book_ids = self.__find_book_ids(keys, sep, page)
            if code != 200:
                raise error.error_and_message(code, msg)

            book_infos = []
            for book_id in book_ids:
                #cursor = self.conn.execute(
                #    "SELECT book_info FROM new_store WHERE book_id = '%s'; " % book_id
                #)
                #rows = cursor.fetchall()
                rows = session.query(Store_table).filter(Store_table.book_id == book_id).all()
                if len(rows) == 0:
                    raise error.error_non_exist_book_id(book_id)
                book_infos.append(json.loads(rows[0].book_info))
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e)), []

        return 200, "ok", book_infos

    def find_in_store(self, store_id: str, keys: list, sep: bool, page: int) -> (int, str, list):
        session = self.conn
        try:
            if not self.store_id_exist(store_id):
                raise error.error_non_exist_store_id(store_id)

            code, msg, book_ids = self.__find_book_ids(keys, sep, page, store_id)
            if code != 200:
                raise error.error_and_message(code, msg)

            book_infos = []
            for book_id in book_ids:
                #cursor = self.conn.execute(
                #    "SELECT book_info, stock_level FROM new_store WHERE book_id = '%s' and store_id = '%s'; " % (book_id, store_id)
                #)
                #rows = cursor.fetchall()
                rows = session.query(Store_table).filter(Store_table.book_id == book_id, Store_table.store_id == store_id).all()
                if len(rows) == 0:
                    raise error.error_non_exist_book_id(book_id)
                book_infos.append(json.loads(rows[0].book_info).update(stock_level=rows[0].stock_level))
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e)), []

        return 200, "ok", book_infos