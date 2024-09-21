import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from database.models import ConfigEmoji

Base = declarative_base()
logger = logging.getLogger("discord_bot")


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

    @contextmanager
    def dp_session(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            session.rollback()
            raise e
        finally:
            session.close()
