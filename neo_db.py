from typing import Dict, List

from exceptions import WrongPigeonGenderException
from utils import cislo_krouzku_full_from_id, pigeon_id_from_cislo_krouzku_full, split_pigeon_id


class NeoDb:

    @staticmethod
    def get_pigeon_by_id(db, pigeon_id) -> Dict[str, any]:
        q = """
            MATCH (p:Pigeon {id: $id })
            RETURN p AS pigeon
        """
        data = db.run(q, id=pigeon_id).data()
        if data:
            return data[0]['pigeon']


    @staticmethod
    def get_pigeons_by_user(db, user_id) -> List:
        q = """
        MATCH (p:Pigeon)
        WHERE p.user_id = $user_id
        WITH p ORDER BY p.plemeno, p.barva, p.id
        RETURN p AS pigeon
        """
        data = db.run(q, user_id=user_id).data()
        return data


    @staticmethod
    def get_mother_of_pigeon(db, pigeon_id) -> Dict[str, any]:
        q = """
            MATCH (m:Pigeon)-[:MATKA]->(:Pigeon {id: $id }) 
            RETURN m AS mother
        """
        data = db.run(q, id=pigeon_id).data()
        if data:
            return data[0]["mother"]

    @staticmethod
    def get_father_of_pigeon(db, pigeon_id) -> Dict[str, any]:
        q = """
            MATCH (f:Pigeon)-[:OTEC]->(:Pigeon {id: $id }) 
            RETURN f AS father
        """
        data = db.run(q, id=pigeon_id).data()
        if data:
            return data[0]["father"]

    @staticmethod
    def add_parent(db, pigeon_id, parent_id, parent_gender):
        result = db.run('MATCH (a:Pigeon) WHERE a.id = $id RETURN a AS pigeon', id=parent_id)
        parent_data = result.data()
        if len(parent_data) == 1:
            if parent_data[0].get('pigeon').get("pohlavi") != parent_gender.marking:
                raise WrongPigeonGenderException(parent_gender.assoc_relationship, parent_data[0].get('pigeon').get("pohlavi"))
        # parent isnt in db yet
        else:
            user_id, cislo_krouzku, rocnik = split_pigeon_id(parent_id)
            data = {
                'id': parent_id,
                'pohlavi': parent_gender.marking,
                'cislo_krouzku': cislo_krouzku,
                'rocnik': rocnik
            }
            db.run('CREATE (p:Pigeon $data )', data=data)

        relationship = parent_gender.assoc_relationship
        q = f"""MATCH
                (a:Pigeon),
                (b:Pigeon)
                WHERE a.id = $parent_id AND b.id = $pigeon_id
                CREATE (a)-[r:{relationship}]->(b)
            """
        db.run(q, parent_id=parent_id, pigeon_id=pigeon_id)

    @staticmethod
    def remove_parent(db, pigeon_id: int, parent_id: int, parent_gender):
        r = parent_gender.assoc_relationship
        q = f"""
            MATCH (:Pigeon {{id: "{parent_id}"}} )-[r:{r}]->(:Pigeon {{id: "{pigeon_id}"}})
            DELETE r
        """
        db.run(q).data()

    @staticmethod
    def replace_parent(db, pigeon_id, old_parent_id, new_parent_id, parent_gender):
        NeoDb.remove_parent(db,
                            pigeon_id=pigeon_id,
                            parent_id=old_parent_id,
                            parent_gender=parent_gender
                            )
        NeoDb.add_parent(db,
                         pigeon_id=pigeon_id,
                         parent_id=new_parent_id,
                         parent_gender=parent_gender
                         )

    @staticmethod
    def update_parent(db, user_id, pigeon_id, db_parent, form_parent_ckf, parent_gender):
        if db_parent:
            # pokud se změní matka či otec, rozvázat vztah s původním a přidat nový
            if form_parent_ckf != cislo_krouzku_full_from_id(db_parent.get("id")):
                if form_parent_ckf:
                    # replace father
                    new_parent_id = pigeon_id_from_cislo_krouzku_full(form_parent_ckf, user_id)
                    NeoDb.replace_parent(db,
                                         pigeon_id=pigeon_id,
                                         old_parent_id=db_parent.get('id'),
                                         new_parent_id=new_parent_id,
                                         parent_gender=parent_gender)
                else:
                    # remove
                    NeoDb.remove_parent(db,
                                        pigeon_id=pigeon_id,
                                        parent_id=db_parent.get('id'),
                                        parent_gender=parent_gender)
        else:
            if form_parent_ckf:
                # add father
                new_parent_id = pigeon_id_from_cislo_krouzku_full(form_parent_ckf, user_id)
                NeoDb.add_parent(db,
                                 pigeon_id=pigeon_id,
                                 parent_id=new_parent_id,
                                 parent_gender=parent_gender)

    @staticmethod
    def update_pigeon_data(db, pigeon_id, pigeon_data):
        q = f"""
            MATCH (p:Pigeon {{ id: '{pigeon_id}' }})
        """
        for key, val in pigeon_data.items():
            q = q + f"SET p.{key} = '{val}'"
        db.run(q)

    @staticmethod
    def get_ancestor_paths(db, pigeon_id):
        q = f"""
            MATCH path=((:Pigeon {{id : '{pigeon_id}'}})<-[r*0..4]-(p:Pigeon)) return path
        """
        result = db.run(q)
        data = result.data()
        return data

    @staticmethod
    def calculate_inbreeding(db, pigeonID):
        q = """
            MATCH (a:Pigeon {id : $id}) MATCH (b:Pigeon  {id : $id})
            OPTIONAL MATCH (a)<-[p1*..10]-(common_ancestor: Pigeon)-[p2*..10]->(b)
            WITH size(p1) + size(p2) AS path_length
            RETURN DISTINCT path_length
        """
        result =db.run(q, id=pigeonID)

        inbreeding_coef = 0
        for item in result.data():
            if item["path_length"]:
                inbreeding_coef += (1/2)**item["path_length"]
        return inbreeding_coef

