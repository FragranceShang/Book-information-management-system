import psycopg2
import click
from psycopg2 import extras
from flask import current_app, g
from flask.cli import with_appcontext

# Connect to your postgres DB
def connect_db():
    if 'conn' not in g:
        try:
            g.conn = psycopg2.connect(cursor_factory = psycopg2.extras.DictCursor,
                                    database='bookstore', user='postgres',
                                    password='20021206', host='127.0.0.1', port=5432)
        except(Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)
    return g.conn
'''
#删除数据库
def drop_db():
    conn = psycopg2.connect(
        database='bookstore', 
        user='postgres',
        password='20021206', 
        host='127.0.0.1', 
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute("DROP DATABASE IF EXISTS flask_db")
    conn.commit()
    cursor.close()
    conn.close()
'''
def close_db(e=None):
    conn = g.pop('conn', None)
    if conn is not None:
        conn.commit()
        conn.close()

#创建数据库，如果数据库不在pg_database中
def create_db():
    conn = psycopg2.connect(database='bookstore', user='postgres',
                            password='20021206', host='127.0.0.1', port=5432)
    cur = conn.cursor()
    print('create database!')
    cur.execute("CREATE DATABASE bookstore")
    with current_app.open_resource('schema.sql') as f:
        conn.cursor().execute(f.read().decode('utf8'))
    cur.close()
    conn.close()

def init_db():
    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT * FROM pg_database WHERE datname='bookstore'")
    if cur.fetchone() == None:
        create_db()
    conn.autocommit = False

conn = psycopg2.connect(
        database='bookstore', 
        user='postgres',
        password='20021206', 
        host='127.0.0.1', 
        port="5432"
    )

@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
