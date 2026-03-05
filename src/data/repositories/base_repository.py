from typing import Type
from fastapi import HTTPException
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

async def commit_transaction(db: AsyncSession):
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Commit failed {str(e)}")

async def insert_data(model: Type, db: AsyncSession, **kwargs):
    try:
        stmt = insert(model).values(**kwargs)
        await db.execute(stmt)
        await commit_transaction(db)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(err))
    except SQLAlchemyError as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(err))