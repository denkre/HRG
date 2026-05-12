import json
import requests as requests

from flask import Blueprint, g, request, jsonify

from db_conf import neo_driver, neo_host
from db_conf import r as redis


pigeon_api = Blueprint('app', __name__)


def get_db():
    if 'db' not in g:
        g.neo4j_db = neo_driver.session()

    return g.neo4j_db


@pigeon_api.route('/api/pigeon', methods=['GET'])
def query_pigeons():
    pg_id = request.args.get('id')
    db = get_db()
    q = "MATCH (a:Pigeon) "
    if pg_id:
        q = q + "WHERE a.id = $id "
    q = q + "RETURN a AS pigeon"
    result = db.run(q, id=pg_id)
    return jsonify(result.data())


@pigeon_api.route('/api/pigeon', methods=['PUT'])
def create_pigeon():
    pigeon = json.loads(request.data)
    pg_id = str(pigeon["cislo_krouzku"]) + "-" + str(pigeon["rocnik"])
    db = get_db()
    db.run("CREATE (p:Pigeon {  id: $id,"
                                "cislo_krouzku: $cislo_krouzku,"
                                "rocnik: $rocnik"
           "}) ", id=pg_id, cislo_krouzku=pigeon["cislo_krouzku"], rocnik=pigeon["rocnik"])

    return jsonify(pigeon)


@pigeon_api.route('/api/pigeon', methods=['POST'])
def update_pigeon():
    pigeon = json.loads(request.data)
    if pigeon.get("id"):
        db = get_db()
        q = "MATCH (p:Pigeon) " \
            "WHERE p.id = $id " \
            "SET "
        for key, value in dict(pigeon).items():
            q = q + f"p.{key} = '{value}', "
        q = q[:-2]

        db.run(q, id=pigeon["id"])
    return jsonify(pigeon)


@pigeon_api.route('/api/pigeon', methods=['DELETE'])
def delete_pigeon():
    pigeon = json.loads(request.data)
    if pigeon.get("id"):
        db = get_db()

        db.run("MATCH (a:Pigeon)"
               "WHERE a.id = $id "
               "DELETE a", id=pigeon["id"])

    return jsonify(pigeon)


@pigeon_api.route("/api/get-neograph-pigeon-all")
def get_neograph_pigeon2():
    url = f"{neo_host}/db/neo4j/tx/commit"
    data = {
     "statements": [
                        {
                        "statement": "MATCH (n),()-[r]-() RETURN n,r LIMIT 50" ,
                        "resultDataContents": ["graph"]
                        }
                    ]
    }
    r = requests.post(url, json=data)
    data = r.json()
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@pigeon_api.route("/api/get-neograph-pigeon/")
def get_neograph_pigeon():
    pigeon_id = request.args.get('pigeonID')
    only_ancestors = request.args.get('only_ancestors', False)
    url = f"{neo_host}/db/neo4j/tx/commit"
    if only_ancestors == "true":
        r_key = f"visualize-pedigree-{pigeon_id}"
        statement = f"MATCH path=((p:Pigeon)-[*0..10]->(:Pigeon {{id : '{pigeon_id}'}})) return p, path"
    else:
        r_key = f"visualize-ancestors-{pigeon_id}"
        statement = f"MATCH path=((p:Pigeon)-[*0..10]-(:Pigeon {{id : '{pigeon_id}'}})) return p, path"

    redis_data = redis.get(r_key)
    if redis_data:
        data = json.loads(redis_data)
    else:
        data = {
         "statements": [
                                {
                                f"statement": statement,
                                "resultDataContents": ["graph"]
                                }
                                ]
        }
        r = requests.post(url, json=data)
        data = r.json()
        redis.set(r_key, json.dumps(data), 60)
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
