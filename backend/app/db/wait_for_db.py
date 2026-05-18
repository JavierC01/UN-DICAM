import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db.session import engine


def wait_for_db(max_attempts: int = 30, delay_s: float = 1.0) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_s)


if __name__ == "__main__":
    wait_for_db()
