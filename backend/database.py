import psycopg2

#connecting to Database
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="RAAG",
        user="postgres",
        password="Abhishek",
        port="5433"
    )