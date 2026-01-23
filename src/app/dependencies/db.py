from typing import Annotated

from fastapi import Depends

from app.db import DbHelper, get_db_helper


async def get_session(db_helper: Annotated[DbHelper, Depends(get_db_helper)]):
    """Get db session dependency."""
    async with db_helper.transaction() as session:
        yield session


session_dependency = Depends(get_session)
