from neo4j import GraphDatabase, basic_auth
from mongoengine import StringField, SequenceField, BooleanField
from flask_mongoengine import MongoEngine
from flask_login.mixins import UserMixin
import redis


neo_driver = GraphDatabase.driver("bolt://neo4j:7687", auth=basic_auth("neo4j", "knock-cape-reserve"))
r = redis.Redis(host='redis', port=6379, db=0)
neo_host = 'http://neo4j:7474'
mongo_host = 'mongodb://mongodb:27017/credentials'
mongo_engine = MongoEngine()

class User(mongo_engine.Document):
    id = SequenceField(primary_key=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    is_active = BooleanField(default=True)

    @property
    def is_authenticated(self):
        return self.is_active

    def get_id(self):
        return self.id

    def get_email(self):
        return self.email

    def get_password_hash(self):
        return self.password

    def __str__(self):
        return f"User:{self.email}"
