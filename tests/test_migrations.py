from sqlalchemy import create_engine, inspect


def test_migrations_create_tables(postgres_container, apply_migrations):
    engine = create_engine(postgres_container.get_connection_url())
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "events" in tables
    assert "seats" in tables
    assert "orders" in tables
