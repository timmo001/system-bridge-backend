"""Schedule handler."""
import datetime

from systembridgeshared.base import Base


class Scheduler(Base):
    """Scheduler used to run tasks in the background at specific intervals."""

    def __init__(self, interval):
        """Initialise."""
        super().__init__()
        self.interval = interval
        self.next_run = datetime.datetime.now()

    def get_next_run(self):
        """Get next run."""
        return self.next_run

    def update_next_run(self):
        """Update next run."""
        self.next_run = datetime.datetime.now() + datetime.timedelta(seconds=self.interval)
