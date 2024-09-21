from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import Bot_config

Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    channel_id = Column(String)
    message_id = Column(String, unique=True)
    content = Column(String)
    timestamp = Column(DateTime)


def init_db():
    engine = create_engine(Bot_config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
