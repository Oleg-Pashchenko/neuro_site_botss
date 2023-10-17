from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
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
    id_id = Column(Integer, primary_key=True)
    __tablename__ = 'messages'
    id = Column(String(300))
    message = Column(String(10000))
    lead_id = Column(Integer, ForeignKey('leads.id'))
    is_bot = Column(Boolean)


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
    block_statuses = []

    def __init__(self, pipeline_id, user_id):
        self._get_data_from_amocrm_db_settings(user_id)
        self._get_data_from_amocrm_db_pipelines(pipeline_id)
        self._get_data_from_amocrm_db_statuses(pipeline_id)

    def _get_data_from_amocrm_db_statuses(self, pipeline_id):
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database='avatarex',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM users_application_statuses WHERE pipeline_id_id=%s", (pipeline_id,))
        resp = cur.fetchall()
        conn.close()
        statuses = []
        for r in resp:
            if r[4] is False:
                statuses.append(int(r[0]))
        self.block_statuses = statuses

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
        self.tokens = int(resp[4])
        self.temperature = float(resp[5])
        self.voice = bool(resp[6])

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
        cur.execute('SELECT * FROM users_application_chatgpt_settings WHERE user_id_id=%s;', (user_id,))
        info2 = cur.fetchone()
        self.openai_api_key = info2[1]
        conn.close()
        self.user, self.password, self.host, self.amo_key = info[2], info[3], info[1], info[4]


# Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
