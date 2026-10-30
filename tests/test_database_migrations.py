from sqlalchemy import create_engine, inspect, text

from scripts.migrate_profile_skills import migrate_workflow_schema


def test_profile_skills_migration_adds_column_once():
    engine = create_engine('sqlite:///:memory:')
    try:
        with engine.begin() as connection:
            connection.execute(text(
                'CREATE TABLE student_profiles (id INTEGER PRIMARY KEY)'
            ))
            connection.execute(text(
                'CREATE TABLE resumes (id INTEGER PRIMARY KEY)'
            ))

        assert migrate_workflow_schema(engine) is True
        assert migrate_workflow_schema(engine) is False
        assert 'skills' in {
            column['name']
            for column in inspect(engine).get_columns('student_profiles')
        }
        assert {'source_type', 'source_url'} <= {
            column['name']
            for column in inspect(engine).get_columns('resumes')
        }
    finally:
        engine.dispose()
