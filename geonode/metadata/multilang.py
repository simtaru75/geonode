
from django.conf import settings

MULTILANG_ANNOTATION = "geonode:multilang"


def is_multilang(fieldname: str, jsonschema: dict) -> bool:
    return jsonschema[fieldname].get(MULTILANG_ANNOTATION, False)


def get_2letters_languages():
    return [l.split("-")[0] for l,_ in settings.LANGUAGES]


def get_multilang_field_names(base_name):
    return ((lang, f"{base_name}_multilang_{lang}") for lang in get_2letters_languages())