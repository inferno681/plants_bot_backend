from typing import Annotated

from fastapi import Depends

from app.db import DbHelper, get_db_helper


async def get_session(db_helper: Annotated[DbHelper, Depends(get_db_helper)]):
    """Get db session dependency."""
    return db_helper.transaction()


session_dependency = Depends(get_session)
