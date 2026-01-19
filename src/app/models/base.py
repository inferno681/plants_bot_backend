from datetime import datetime, timezone

from beanie import Document, Insert, Replace, SaveChanges, before_event


class BaseDocument(Document):
    """Base document with settings and created_at, updated_at timestamps."""

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @before_event(Insert)
    def on_insert_set_timestamps(self):
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.updated_at = now

    @before_event([Replace, SaveChanges])
    def on_update_set_timestamps(self):
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        use_state_management = True
        exclude_none = True
