"""This module implements a simple database migration system for managing schema changes in a PostgreSQL database. It defines a `MigrationFile` data class to represent individual migration files, and provides functions to discover migration files in a specified directory, apply pending migrations to the database, and ensure that the migration history is properly tracked in a `schema_migrations` table. The module also includes logic to validate applied migrations against their original SQL content using checksums, preventing accidental changes to already applied migrations.    Migration files are expected to follow a specific naming convention (`<version_number>_<name>.sql`) and contain valid SQL statements. The module handles splitting SQL files into individual statements while correctly accounting for comments and string literals, ensuring that complex SQL scripts can be executed without issues.    This migration system is designed to be simple and self-contained, making it easy to integrate into applications that require basic schema migration capabilities without relying on external libraries or tools.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
 
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
 
 
_logger = logging.getLogger("uvicorn.error")
_MIGRATION_FILE_RE = re.compile(r"^(?P<version_number>\d{8,14})_(?P<name>[a-z0-9_]+)\.sql$")
_DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent / "versions"
 
 
@dataclass(frozen=True, slots=True)
class MigrationFile:
    """Data class representing a database migration file. It contains the identifier, version number, name, checksum, SQL content, and file path of the migration. This class is used to encapsulate all relevant information about a migration file for processing and applying migrations to the database."""
    identifier: str
    version_number: str
    name: str
    checksum: str
    sql: str
    path: Path
 
 
def discover_migrations(migrations_dir: Path | None = None) -> list[MigrationFile]:
    """Discover migration files in the specified directory. This function scans the given directory for SQL files that match the expected naming convention, validates their contents, and returns a list of MigrationFile objects representing each valid migration. It ensures that there are no duplicate identifiers and that each migration file contains executable SQL statements.   If the directory does not exist or is not a directory, it raises an appropriate exception. The function also computes a checksum for each migration file to detect any changes to applied migrations in future runs.    Args:
        migrations_dir: An optional Path to the directory containing migration files. If None, it defaults to the "versions" subdirectory relative to this script.    Returns:
        A list of MigrationFile objects representing the discovered migrations, sorted by their version numbers.    Raises:
        FileNotFoundError: If the specified migration directory does not exist.
        NotADirectoryError: If the specified migration path is not a directory.
        ValueError: If any migration file has an invalid name, is empty, or if there are duplicate migration identifiers.
    """
    directory = migrations_dir or _DEFAULT_MIGRATIONS_DIR
    if not directory.exists():
        raise FileNotFoundError(f"Migration directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Migration path is not a directory: {directory}")
 
    migrations: list[MigrationFile] = []
    seen_identifiers: set[str] = set()
 
    for path in sorted(directory.glob("*.sql")):
        match = _MIGRATION_FILE_RE.match(path.name)
        if not match:
            raise ValueError(
                "Invalid migration filename "
                f"{path.name!r}. Expected '<version>_<name>.sql' with lowercase snake_case."
            )
 
        identifier = path.stem
        if identifier in seen_identifiers:
            raise ValueError(f"Duplicate migration identifier found: {identifier}")
        seen_identifiers.add(identifier)
 
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            raise ValueError(f"Migration file is empty: {path}")
 
        migrations.append(
            MigrationFile(
                identifier=identifier,
                version_number=match.group("version_number"),
                name=match.group("name"),
                checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
                sql=sql,
                path=path,
            )
        )
 
    return migrations
 
 
async def apply_migrations(
    conn: AsyncConnection,
    migrations_dir: Path | None = None,
) -> None:
    """Apply pending migrations to the database. This function connects to the database and applies any migrations that have not yet been applied, as determined by the records in the `schema_migrations` table. It ensures that each migration is applied in order and that the migration history is properly tracked. If a migration has already been applied, it validates that the checksum matches the original SQL content to detect any changes.    Args:
        conn: An active AsyncConnection to the database where migrations should be applied.
        migrations_dir: An optional Path to the directory containing migration files. If None, it defaults to the "versions" subdirectory relative to this script.    Raises:
        RuntimeError: If a migration has already been applied but its checksum does not match the original SQL content, indicating that the migration file has been modified after being applied.
    """
    migrations = discover_migrations(migrations_dir)
    await _ensure_schema_migrations_table(conn)
 
    result = await conn.execute(
        text(
            """
            SELECT version, version_number, name, checksum
            FROM schema_migrations
            """
        )
    )
    applied = {
        row.version: {
            "version_number": row.version_number,
            "name": row.name,
            "checksum": row.checksum,
        }
        for row in result
    }
 
    for migration in migrations:
        existing = applied.get(migration.identifier)
        if existing is not None:
            await _validate_or_backfill_migration_record(conn, migration, existing)
            continue
 
        statements = _split_sql_statements(migration.sql)
        if not statements:
            raise ValueError(f"Migration {migration.identifier} contains no executable SQL statements.")
 
        _logger.info("Applying DB migration: %s", migration.identifier)
        for statement in statements:
            await conn.exec_driver_sql(statement)
 
        await conn.execute(
            text(
                """
                INSERT INTO schema_migrations (version, version_number, name, checksum)
                VALUES (:version, :version_number, :name, :checksum)
                """
            ),
            {
                "version": migration.identifier,
                "version_number": migration.version_number,
                "name": migration.name,
                "checksum": migration.checksum,
            },
        )
        _logger.info("Applied DB migration: %s", migration.identifier)
 
 
async def _ensure_schema_migrations_table(conn: AsyncConnection) -> None:
    """Ensure that the schema_migrations table exists in the database. This function creates the `schema_migrations` table if it does not already exist, and adds any missing columns that are required for tracking migration history. The table is used to store records of applied migrations, including their version identifiers, version numbers, names, checksums, and timestamps of when they were applied.    Args:
        conn: An active AsyncConnection to the database where the `schema_migrations` table should be ensured.    Raises:
        RuntimeError: If there is an error creating the `schema_migrations` table or adding necessary columns.
    """
    await conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(128) PRIMARY KEY,
            version_number VARCHAR(32),
            name VARCHAR(255),
            checksum VARCHAR(64),
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    await conn.exec_driver_sql(
        "ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS version_number VARCHAR(32)"
    )
    await conn.exec_driver_sql(
        "ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS name VARCHAR(255)"
    )
    await conn.exec_driver_sql(
        "ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum VARCHAR(64)"
    )
 
 
async def _validate_or_backfill_migration_record(
    conn: AsyncConnection,
    migration: MigrationFile,
    existing: dict[str, str | None],
) -> None:
    """Validate an existing migration record against the migration file, or backfill missing information. This function checks if the checksum of an already applied migration matches the checksum of the current migration file. If there is a mismatch, it raises a RuntimeError to prevent potential issues caused by modified migration files. If the record is missing version number, name, or checksum, it backfills this information in the database to ensure that the migration history is complete and accurate.    Args:
        conn: An active AsyncConnection to the database where the migration record should be validated or backfilled.
        migration: The MigrationFile object representing the migration being validated.
        existing: A dictionary containing the existing migration record from the database, with keys "version_number", "name", and "checksum".    Raises:
        RuntimeError: If the checksum of the existing migration record does not match the checksum of the migration file, indicating that the migration file has been modified after being applied.
    """
    checksum = existing.get("checksum")
    if checksum:
        if checksum != migration.checksum:
            raise RuntimeError(
                "Migration checksum mismatch for "
                f"{migration.identifier}. Refusing to continue because an applied SQL file changed."
            )
        if existing.get("version_number") and existing.get("name"):
            return
 
    await conn.execute(
        text(
            """
            UPDATE schema_migrations
            SET version_number = COALESCE(version_number, :version_number),
                name = COALESCE(name, :name),
                checksum = COALESCE(checksum, :checksum)
            WHERE version = :version
            """
        ),
        {
            "version": migration.identifier,
            "version_number": migration.version_number,
            "name": migration.name,
            "checksum": migration.checksum,
        },
    )
 
 
def _split_sql_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements. This function takes a string containing SQL commands and splits it into separate statements based on semicolons, while correctly handling comments, string literals, and dollar-quoted strings. It ensures that semicolons within comments or string literals do not cause incorrect splitting of statements. The resulting list contains clean SQL statements that can be executed individually.    Args:
        sql: A string containing the SQL script to be split into statements.    Returns:
        A list of individual SQL statements extracted from the input script, with leading and trailing whitespace removed. Empty statements are filtered out.
    """
    statements: list[str] = []
    current: list[str] = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    dollar_quote: str | None = None
 
    while i < len(sql):
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < len(sql) else ""
 
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                current.append(char)
            i += 1
            continue
 
        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
 
        if dollar_quote is not None:
            if sql.startswith(dollar_quote, i):
                current.append(dollar_quote)
                i += len(dollar_quote)
                dollar_quote = None
                continue
            current.append(char)
            i += 1
            continue
 
        if in_single_quote:
            current.append(char)
            if char == "'" and next_char == "'":
                current.append(next_char)
                i += 2
                continue
            if char == "'":
                in_single_quote = False
            i += 1
            continue
 
        if in_double_quote:
            current.append(char)
            if char == '"' and next_char == '"':
                current.append(next_char)
                i += 2
                continue
            if char == '"':
                in_double_quote = False
            i += 1
            continue
 
        if char == "-" and next_char == "-":
            in_line_comment = True
            i += 2
            continue
 
        if char == "/" and next_char == "*":
            in_block_comment = True
            i += 2
            continue
 
        if char == "'":
            in_single_quote = True
            current.append(char)
            i += 1
            continue
 
        if char == '"':
            in_double_quote = True
            current.append(char)
            i += 1
            continue
 
        if char == "$":
            tag_end = sql.find("$", i + 1)
            if tag_end != -1:
                candidate = sql[i : tag_end + 1]
                if re.fullmatch(r"\$[A-Za-z0-9_]*\$", candidate):
                    dollar_quote = candidate
                    current.append(candidate)
                    i = tag_end + 1
                    continue
 
        if char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue
 
        current.append(char)
        i += 1
 
    trailing_statement = "".join(current).strip()
    if trailing_statement:
        statements.append(trailing_statement)
    return statements
 
 