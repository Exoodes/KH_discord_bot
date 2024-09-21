from sqlalchemy import Column, Enum, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import Bot_config

Base = declarative_base()


class Category(Base):
    """Tabulka pro vybírání kategorií"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    emoji = Column(String, unique=True, nullable=False)
    is_public = Column(bool, default=True, nullable=False)


class UserCategory(Base):
    """Tabulka pro ukládání kategorií uživatelů"""

    __tablename__ = "user_categories"

    user_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)
    category = relationship("Category")


class CategoryRequest(Base):
    """Tabulka pro žádosti o kategorii od uživatelů"""

    __tablename__ = "category_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    request_message_id = Column(Integer, nullable=False)
    status = Column(Enum("pending", "approved", "declined"), default="pending")
    category = relationship("Category")


class BotMessage(Base):
    __tablename__ = "bot_messages"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    message_type = Column(String, nullable=False)


class ConfigEmoji(Base):
    __tablename__ = "config_emojis"

    id = Column(Integer, primary_key=True)
    purpose = Column(String, unique=True, nullable=False)
    emoji_id = Column(String, nullable=False)


def init_db():
    engine = create_engine(Bot_config.DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
