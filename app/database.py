from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from config import settings


SQLALCHEMY_DATABASE_URL = 'postgresql://gchxeydy:8HJbQfw3Al8lzbICFDaflpi4Sk2JzmdI@raja.db.elephantsql.com/gchxeydy'

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
                
while True:
    try:
        conn = psycopg2.connect(host='localhost', database='eventful', user='postgres',
                                password='genesix2580', cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print('Connection to database was successful')
        break
    except Exception as error:
        print('connecting to database failed')
        print('Error:', error)
        time.sleep(3)