from sqlalchemy.exc import SQLAlchemyError
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from be.model.store import User_table, User_store, Store_table, New_order, New_order_detail, History_order, Invert_index

class Order (db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def cancel_order(self, order_id, end_status = 0):
        session = self.conn
        try:
            #cursor = self.conn.execute(
            #    "DELETE FROM new_order WHERE order_id = '%s' RETURNING order_id, user_id, store_id ,total_price, order_time ;" % (order_id)
            #)
            row = session.query(New_order).filter(New_order.order_id == order_id).delete()
            if len(row) == 0:
                self.conn.rollback()
                return error.error_invalid_order_id(order_id)
            #row = cursor.fetchone()
            order = {
                "order_id": row[0].order_id,
                "user_id": row[0].user_id,
                "store_id": row[0].store_id,
                "total_price": row[0].total_price,
                "order_time": row[0].order_time,
                "status": end_status
            }
            books = []
            #cursor = self.conn.execute(
            #    "DELETE FROM new_order_detail WHERE order_id = '%s' RETURNING book_id, count ;" % (order_id)
            #)
            rows = session.query(New_order_detail).filter(New_order_detail.order_id == order_id).delete()
            #rows = cursor.fetchall()
            for row in rows:
                book = {
                    "book_id": row.book_id,
                    "count": row.count
                }
                if end_status == 0:
                    #cursor = self.conn.execute (
                    #    "UPDATE store set stock_level = stock_level + '%d' WHERE store_id = '%s' and book_id = '%s' ;"
                    #    % (book["count"], order["store_id"], book["book_id"])
                    #)
                    _row = session.query(Store_table).filter(Store_table.store_id == order["store_id"], Store_table.book_id == book["book_id"]).update({"stock_level": Store_table.stock_level + book["count"]})
                    if len(_row) == 0:
                        self.conn.rollback()
                        return error.error_non_exist_book_id(book["book_id"]) + (order_id,)
                    self.conn.commit()
                books.append(book)

            order["books"] = books
            #self.conn.execute(
            #    "INSERT INTO history_order(order_id, store_id, user_id, status, total_price, order_time) "
            #    "VALUES(?, ?, ?, ?, ?, ?)",
            #    (order["order_id"], order["store_id"], order["user_id"], order["status"], order["total_price"], order["order_time"])
            #)
            history_order = History_order(order["order_id"], order["store_id"], order["user_id"], order["status"], order["total_price"], order["order_time"])
            session.add(history_order)
            session.commit()
            #self.mongo['history_order'].insert_one(order)
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"