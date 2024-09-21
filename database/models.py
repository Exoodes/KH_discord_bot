import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql.sqltypes import Boolean

Base = declarative_base()


class BotMessageType(enum.Enum):
    CategoryChooser = 1


class BotMessage(Base):
    __tablename__ = "bot_messages"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    message_type = Column(Enum(BotMessageType), nullable=False)


class Category(Base):
    """Tabulka pro vybírání kategorií"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)
    name = Column(String, unique=True, nullable=False)
    emoji = Column(String, unique=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)


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


class ConfigEmoji(Base):
    __tablename__ = "config_emojis"

    id = Column(Integer, primary_key=True)
    purpose = Column(String, unique=True, nullable=False)
    emoji_id = Column(String, nullable=False)


class Database:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.init_emojis()

    def get_session(self):
        return self.Session()

    def init_emojis(self):
        session = self.get_session()
        try:
            existing_emojis = session.query(ConfigEmoji.purpose).all()
            existing_purposes = {emoji.purpose for emoji in existing_emojis}

            emojis_to_add = [
                ConfigEmoji(purpose="accept", emoji_id="✅"),
                ConfigEmoji(purpose="decline", emoji_id="❌"),
            ]

            for emoji in emojis_to_add:
                if emoji.purpose not in existing_purposes:
                    session.add(emoji)

            session.commit()
        finally:
            session.close()
