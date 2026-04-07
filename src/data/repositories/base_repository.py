"""This module defines the base repository functions for interacting with the database using SQLAlchemy's asynchronous session. It includes utility functions for committing transactions and inserting data into the database while handling exceptions that may arise during these operations. The commit_transaction function attempts to commit the current transaction and rolls back if any exceptions occur, providing detailed error messages. The insert_data function allows for inserting new records into the database based on a specified model and keyword arguments, while also handling integrity errors and other SQLAlchemy-related exceptions to ensure data integrity and provide meaningful feedback in case of errors.     By centralizing these common database operations in a base repository module, we can promote code reuse and maintain consistency across different parts of the application that interact with the database. This approach also helps to simplify error handling and improve the overall robustness of the application's data access layer."""

from typing import Any

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions.exceptions import AppException, ConflictException


async def commit_transaction(db: AsyncSession) -> None:
    """Commit the current transaction in the database session. This function attempts to commit the transaction and handles any exceptions that may occur during the commit process. If an IntegrityError occurs (e.g., due to a unique constraint violation), it rolls back the transaction and raises a ConflictException with details of the error. For any other SQLAlchemy-related errors, it also rolls back the transaction and raises a generic AppException with the error details.    Args:
    db: An instance of AsyncSession representing the current database session.    Raises:
    ConflictException: If an integrity error occurs during the commit operation, such as a unique constraint violation.    AppException: If any other SQLAlchemy-related error occurs during the commit operation."""
    try:
        await db.commit()
    except Exception as err:
        await db.rollback()
        raise AppException(detail=f"Commit failed {str(err)}") from err


async def insert_data(model: type[Any], db: AsyncSession, **kwargs: Any) -> None:
    """Insert data into the database using the specified model and keyword arguments. This function attempts to insert a new record into the database based on the provided model and data. If an integrity error occurs (e.g., due to a unique constraint violation), it rolls back the transaction and raises a ConflictException with details of the error. For any other SQLAlchemy-related errors, it also rolls back the transaction and raises a generic AppException with the error details.    Args:       model: The SQLAlchemy model class representing the database table into which the data should be inserted.    db: An instance of AsyncSession for interacting with the database.    **kwargs: Keyword arguments representing the data to be inserted, where keys correspond to column names in the database table.    Raises:       ConflictException: If an integrity error occurs during the insert operation, such as a unique constraint violation.    AppException: If any other SQLAlchemy-related error occurs during the insert operation."""
    try:
        stmt = insert(model).values(**kwargs)
        await db.execute(stmt)
        await commit_transaction(db)
    except IntegrityError as err:
        await db.rollback()
        raise ConflictException(detail=str(err)) from err
    except SQLAlchemyError as err:
        await db.rollback()
        raise AppException(detail=str(err)) from err
