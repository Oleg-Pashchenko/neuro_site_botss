from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os
import dotenv

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
    id = Column(Integer, primary_key=True)
    message = Column(String(10000))
    lead_id = Column(Integer, ForeignKey('leads.id'))



#Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
