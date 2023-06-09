from sqlalchemy.exc import SQLAlchemyError
import json

from be.model import error
from be.model import db_conn
from be.model.order import Order
from .tokenize import Tokenizer
from be.model.store import User_table, User_store, Store_table, New_order, New_order_detail, History_order, Invert_index

class Seller(db_conn.DBConn):

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            book_info = json.loads(book_json_str)
            tokenizer = Tokenizer()
            #self.conn.execute("INSERT into new_store(store_id, book_id, book_info, stock_level, price)"
            #                  "VALUES (?, ?, ?, ?, ?)", (store_id, book_id, book_json_str, stock_level, book_info.get("price")))
            store = Store_table(store_id = store_id, book_id = book_id, book_info = book_json_str, stock_level = stock_level, price = book_info.get("price"))
            session.add(store)
            session.commit()
            ctx = []
            def insert(raw):
                if not isinstance(raw, str):
                    return
                tokens = tokenizer.forward(raw)
                for token in tokens:
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})

            if "title" in book_info:
                token = book_info["title"]
                if isinstance(token, str):
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "author" in book_info:
                code, token = tokenizer.parse_author(book_info["author"])
                if code == 200:
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "publisher" in book_info:
                token = book_info["publisher"]
                if isinstance(token, str):
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "translator" in book_info:
                token = book_info["translator"]
                if isinstance(token, str):
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "tags" in book_info:
                tags = book_info["tags"]
                if isinstance(tags, list):
                    for tag in tags:
                        ctx.append({"key_ctx": tag, "store_id": store_id, "book_id": book_id})
            if "author_intro" in book_info:
                insert(book_info["author_intro"])
            if "book_intro" in book_info:
                insert(book_info["book_intro"])
            if "content" in book_info:
                insert(book_info["content"])

            for c in ctx:
                invert_index = Invert_index(search_key = c["key_ctx"], store_id = c["store_id"], book_id = c["book_id"])
                session.add(invert_index)
                #self.conn.execute("INSERT into invert_index(search_key, book_id, book_title, book_author)"
                #                  "VALUES (?, ?, ?, ?)", (c["key_ctx"], book_id, book_info.get("title"), book_info.get("author")))

            session.commit()
        except SQLAlchemyError as e:
            print(str(e))
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(str(e))
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            #self.conn.execute("UPDATE new_store SET stock_level = stock_level + ? "
            #                  "WHERE store_id = ? AND book_id = ?", (add_stock_level, store_id, book_id))
            session.query(Store_table).filter(Store_table.store_id == store_id, Store_table.book_id == book_id).update({"stock_level": Store_table.stock_level + add_stock_level})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        session = self.conn
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            #self.conn.execute("INSERT into user_store(store_id, user_id)"
            #                  "VALUES (?, ?)", (store_id, user_id))
            user_store = User_store(user_id = user_id, store_id = store_id)
            session.add(user_store)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e))
        return 200, "ok"

    def send_books(self, store_id: str, order_id: str) -> (int, str):
        session = self.conn
        try:
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.order_id_exist(order_id):
                return error.error_non_exist_order_id(order_id)
            #cursor = self.conn.execute(
            #    "SELECT status FROM new_order WHERE order_id = '%s';" % order_id
            #)
            row = session.query(New_order).filter(New_order.order_id == order_id).all()
            #row = cursor.fetchone()
            if len(row) == 0:
                return error.error_non_exist_order_id(order_id)
            status = row[0].status
            if status != 2:
                return error.error_invalid_order_status(order_id)
            session.query(New_order).filter(New_order.order_id == order_id).update({"status": 3})
            #self.conn.execute(
            #    "UPDATE new_order set status = 3 WHERE order_id = '%s';" % order_id
            #)

            session.commit()
        except SQLAlchemyError as e:
            print(e)
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e))
        return 200, "ok"
