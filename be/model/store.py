'''
import logging
import os
import sqlite3 as sqlite
from sqlalchemy import Column, String, create_engine, Integer, Text, Date, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, session, declarative_base
import time

#from sqlalchemy import create_engine,MetaData
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

#from pymongo import MongoClient


class Store:
    database: str

    def __init__(self):
        self.engine = create_engine('postgresql://postgres:yingge@127.0.0.1:5432/testdb', pool_size = 8, pool_recycle = 60 * 30)
        self.DbSession = sessionmaker(bind=self.engine)
        self.conn = self.DbSession()
        self.base = declarative_base()
        self.init_tables()

    def init_tables(self):
        try:
            conn = self.get_db_conn()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS user ("
                "user_id TEXT PRIMARY KEY, password TEXT NOT NULL, "
                "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS user_store("
                "user_id TEXT, store_id, PRIMARY KEY(user_id, store_id));"
            )

            #conn.execute(
            #    "CREATE TABLE IF NOT EXISTS store( "
            #    "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER"
            #    " PRIMARY KEY(store_id, book_id))"
            #)

            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_store( "
                "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER, price INTEGER"
                " PRIMARY KEY(store_id, book_id))"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order( "
                "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT, "
                "status INTEGER DEFAULT 1, total_price INTEGER, order_time INTEGER )"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order_detail( "
                "order_id TEXT, book_id TEXT, count INTEGER,  "
                "PRIMARY KEY(order_id, book_id))"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS history_order( "
                "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT, "
                "status INTEGER DEFAULT 1, total_price INTEGER, order_time INTEGER )"
            )

            conn.execute(
                "CREATE TABLE IF NOT EXISTS invert_index( "
                "search_key TEXT, search_id serial, book_id TEXT, "
                "book_title TEXT, book_author TEXT, "
                "PRIMARY KEY(search_key, search_id))"
            )

            conn.commit()
        except SQLAlchemyError as e:
            logging.error(e)
            conn.rollback()

    def get_db_conn(self):
        return self.conn

    #def get_db_mongo(self):
    #    return self.mongodb


database_instance: Store = Store()


def init_database():
    global database_instance
    database_instance = Store()


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()

#def get_db_mongo():
#    global database_instance
#    return database_instance.get_db_mongo()
'''

import logging
import os
import uuid
import sqlalchemy
from sqlalchemy import Column, String, create_engine, Integer, Text, Date
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.ext.declarative import declarative_base
import time
from sqlalchemy import create_engine
from sqlalchemy import Enum,ForeignKey,UniqueConstraint
from sqlalchemy.orm import relationship

from sqlalchemy.exc import SQLAlchemyError



class Store:

    def __init__(self):
        self.engine = create_engine('postgresql://postgres:yingge@127.0.0.1:5432/testdb', pool_size = 8, pool_recycle = 60 * 30)
        self.DbSession = sessionmaker(bind=self.engine)
        self.session = self.DbSession()
        self.base = declarative_base()

    def getEngine(self):
        return self.engine

    def getSession(self):
        return self.session

    def getBase(self):
        return self.base

    def __del__(self):
        self.session.close()

database_instance: Store = Store()

def getDatabaseBase():
    global database_instance
    return database_instance.getBase()

def getDatabaseSession ():
    global database_instance
    return database_instance.getSession()

Base = getDatabaseBase()

class User_table(Base):
    __tablename__ = 'user_table'
    user_id = Column(Text, primary_key=True, unique=True, nullable=False)
    password = Column(Text, nullable=False)
    balance = Column(Integer, nullable=False)
    token = Column(Text)
    terminal = Column(Text)

class User_store (Base):
    __tablename__ = "user_store"

    user_id = Column(Text, primary_key=True, nullable=False)
    store_id = Column(Text, primary_key=True, nullable=False)

class Store_table (Base):
    __tablename__ = "store_table"

    store_id = Column(Text, primary_key=True, nullable=False)
    book_id = Column(Text, primary_key=True, nullable=False)
    book_info = Column(Text, nullable=False)
    stock_level = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

class New_order (Base):
    __tablename__ = "new_order"

    order_id = Column(Text, primary_key=True, nullable=False)
    user_id = Column(Text, nullable=False)
    store_id = Column(Text, nullable=False)
    status = Column(Integer, nullable=False, default = 1)
    total_price = Column(Integer, nullable=False)
    order_time = Column(Integer, nullable=False)

class New_order_detail (Base):
    __tablename__ = "new_order_detail"

    order_id = Column(Text, primary_key=True, nullable=False)
    book_id = Column(Text, primary_key=True, nullable=False)
    count = Column(Integer, nullable=False)

class History_order (Base):
    __tablename__ = "history_order"

    order_id = Column(Text, primary_key=True, nullable=False)
    user_id = Column(Text, nullable=False)
    store_id = Column(Text, nullable=False)
    status = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    order_time = Column(Integer, nullable=False)

class Invert_index (Base):
    __tablename__ = "invert_index"
    id = Column(String, primary_key = True, default = lambda:str(uuid.uuid1()))
    search_key = Column(Text, nullable=False)
    book_id = Column(Text, nullable=False)
    store_id = Column(Text, nullable=False)

def init_database():
    print ("init_database")
    global database_instance
    # database_instance = Database()
    engine = database_instance.getEngine()
    print ("creating tables")
    database_instance.getBase().metadata.create_all(engine)
