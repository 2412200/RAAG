import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()


def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="RAAG",
        user="postgres",
        password="Abhishek",
        port="5433"
    )

def get_users_connection():
    return psycopg2.connect(
        host="localhost",
        database="users",
        user="postgres",
        password="Abhishek",
        port = "5433"
    )

def add_product():
    return psycopg2.connect(
        host="localhost",
        database="product",
        user="postgres",
        password="Abhishek",
        port = "5433"
    )