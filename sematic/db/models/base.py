# Third-party
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join(
                "{}={}".format(column.name, repr(getattr(self, column.name)))
                for column in self.__class__.__table__.columns
            ),
        )
