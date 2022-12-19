from neo4j import GraphDatabase, basic_auth
from mongoengine import StringField, SequenceField, BooleanField
from flask_mongoengine import MongoEngine
import redis


neo_driver = GraphDatabase.driver("bolt://127.0.0.1:7689", auth=basic_auth("neo4j", "knock-cape-reserve"))
r = redis.Redis(host='localhost', port=6381, db=0)
mongo_engine = MongoEngine()

class User(mongo_engine.Document):
    id = SequenceField(primary_key=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    is_active = BooleanField(default=True)

    def is_authenticated(self):
        return self.is_active

    def get_id(self):
        return self.id

    def get_email(self):
        return self.email
