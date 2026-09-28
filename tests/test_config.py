from flightops.config import Settings


def test_settings_default_to_local_sqlite() -> None:
    settings = Settings(database_url=None, db_host=None)
    assert settings.resolved_database_url == "sqlite:///./flightops.db"


def test_settings_build_encoded_postgresql_url_from_secret_parts() -> None:
    settings = Settings(
        database_url=None,
        db_host="database.internal",
        db_name="flightops",
        db_username="flightops user",
        db_password="p@ss/word",
    )
    assert settings.resolved_database_url == (
        "postgresql+psycopg://flightops+user:p%40ss%2Fword@database.internal:5432/flightops"
    )


def test_explicit_database_url_takes_precedence() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://explicit/db",
        db_host="ignored",
        db_username="ignored",
        db_password="ignored",
    )
    assert settings.resolved_database_url == "postgresql+psycopg://explicit/db"
