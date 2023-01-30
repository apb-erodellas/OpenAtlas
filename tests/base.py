import unittest
from pathlib import Path
from typing import Optional

import psycopg2
from flask import url_for

from openatlas import app
from openatlas.models.entity import Entity
from openatlas.models.type import Type


class TestBaseCase(unittest.TestCase):

    def setUp(self) -> None:
        app.testing = True
        app.config.from_pyfile('testing.py')
        self.setup_database()
        self.app = app.test_client()
        self.login('Alice', logout=False)
        with app.app_context():
            with app.test_request_context():
                app.preprocess_request()  # type: ignore
                self.alice_id = 2
                self.precision_type = \
                    Type.get_hierarchy('External reference match')

    def login(self, name: str, logout: bool = True) -> None:
        with app.app_context():
            if logout:
                self.app.get(url_for('logout'))
            self.app.post(
                url_for('login'),
                data={'username': name, 'password': 'test'})

    def setup_database(self) -> None:
        connection = psycopg2.connect(
            database=app.config['DATABASE_NAME'],
            host=app.config['DATABASE_HOST'],
            user=app.config['DATABASE_USER'],
            password=app.config['DATABASE_PASS'],
            port=app.config['DATABASE_PORT'])
        connection.autocommit = True
        self.cursor = connection.cursor()
        for file_name in [
                '1_structure',
                '2_data_model',
                '3_data_web',
                '4_data_type',
                'data_test']:
            with open(
                    Path(app.root_path).parent / 'install' /
                    f'{file_name}.sql', encoding='utf8') as sql_file:
                self.cursor.execute(sql_file.read())


class ApiTestCase(TestBaseCase):

    def setUp(self) -> None:
        super().setUp()
        with open(
                Path(app.root_path).parent / 'install' / 'data_test_api.sql',
                encoding='utf8') as sql_file:
            self.cursor.execute(sql_file.read())


def insert(
        class_: str,
        name: str,
        description: Optional[str] = None) -> Entity:
    entity = Entity.insert(class_, name, description)
    if class_ in ['artifact', 'feature', 'place', 'stratigraphic_unit']:
        entity.link(
            'P53',
            Entity.insert('object_location', f'Location of {name}'))
    return entity


def get_hierarchy(name: str) -> Type:
    return Type.get_hierarchy(name)
