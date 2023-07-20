# Third-party
from sqlalchemy.ext.declarative import declarative_base


class AbstractBase:

    __allow_unmapped__ = True

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join(
                "{}={}".format(column.name, repr(getattr(self, column.name)))
                for column in self.__class__.__table__.columns
            ),
        )


Base = declarative_base(cls=AbstractBase)
