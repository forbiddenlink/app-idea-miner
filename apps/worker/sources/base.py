from abc import ABC, abstractmethod

from packages.core.models import RawPost


class BaseSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    async def fetch(self) -> list[RawPost]:
        """
        Fetch new posts from the source.

        Returns:
            List of RawPost objects. These should be transient (not yet saved
            to the database) so the ingestion runner can handle deduplication
            and persistence centrally.
        """
        pass
