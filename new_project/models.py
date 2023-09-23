from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os
import dotenv
import psycopg2

dotenv.load_dotenv()

engine = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
                       f'@{os.getenv("DB_HOST")}:5432/{os.getenv("DB_NAME")}')

Base = declarative_base()


class Leads(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer)
    status_id = Column(Integer)


class Messages(Base):
    __tablename__ = 'messages'
    id = Column(String(300))
    message = Column(String(10000))
    lead_id = Column(Integer, ForeignKey('leads.id'))


class RequestSettings:
    id = ''
    text = ''
    model = ''
    ft_model = ''
    tokens = ''
    temperature = ''
    voice = ''
    host = ''
    user = ''
    password = ''
    amo_key = ''
    openai_api_key = ''

    def __init__(self, pipeline_id, user_id):
        self._get_data_from_amocrm_db_settings(pipeline_id)
        self._get_data_from_amocrm_db_pipelines(user_id)

    def _get_data_from_amocrm_db_pipelines(self, pipeline_id):
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database='avatarex',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM users_application_amocrm_pipelines WHERE id=%s", (pipeline_id,))
        resp = cur.fetchone()
        conn.close()
        self.id = resp[0]
        self.text = resp[1]
        self.model = resp[2]
        self.ft_model = resp[3]
        self.tokens = resp[4]
        self.temperature = resp[5]
        self.voice = resp[6]

    def _get_data_from_amocrm_db_settings(self, user_id):
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database='avatarex',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM users_application_amocrm_settings WHERE user_id_id=%s;", (user_id,))
        info = cur.fetchone()
        conn.close()
        self.openai_api_key = info[0]
        self.user, self.password, self.host, self.amo_key = info[2], info[3], info[1], info[4]


# Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
