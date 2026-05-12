from exceptions import  *
import re
from enum import Enum


class PigeonGender(Enum):
    HOLUB = ("1.0", "OTEC")
    HOLUBICE = ("0.1", "MATKA")
    
    def __init__(self, marking, assoc_relationship):
        self.marking = marking
        self.assoc_relationship = assoc_relationship
    
    @staticmethod
    def get_gender_from_marking(marking):
        for gender in PigeonGender:
            if gender.marking == marking:
                return gender
        return None


def cislo_krouzku_full_from_id(pigeonID):
    parts = pigeonID.split("-")
    if len(parts)!=3:
        raise WrongPigeonIdFormat(pigeonID)
    return parts[1] + "/" + parts[2]

def user_id_from_pigoen_id(pigeonID):
    parts = pigeonID.split('-')
    if len(parts) != 3:
        raise WrongPigeonIdFormat(pigeonID)
    return int(parts[0])

def split_pigeon_id(pigeonID):
    parts = pigeonID.split('-')
    if len(parts)!=3:
        raise WrongPigeonIdFormat(pigeonID)
    return parts

def pigeon_id_from_cislo_krouzku_full(cislo_krouzku_full, user_id):
    parts = cislo_krouzku_full.split("/")
    if len(parts) != 2:
        raise WrongPigeonIdFormat(cislo_krouzku_full)
    return f'{user_id}-{parts[0]}-{parts[1]}'

def check_pigeon_id_validity(pigeonID):
    pat = re.compile(r"\d+\-[A-Z]+\d+\-\d{2}")
    return re.fullmatch(pat, pigeonID)

