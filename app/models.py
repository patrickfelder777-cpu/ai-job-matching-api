
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    remote: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"JobPosting(id={self.id}, "
            f"title={self.title!r}, "
            f"company={self.company!r})"
        )
