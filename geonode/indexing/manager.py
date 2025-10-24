import logging
from django.conf import settings
from django.contrib.postgres.search import SearchVector

from geonode.base.models import ResourceBase
from geonode.indexing.models import ResourceIndex
from geonode.metadata.multilang import get_2letters_languages, is_multilang, get_multilang_field_names


logger = logging.getLogger(__name__)


class IndexManager:

    def __init__(self):
        self.LANGUAGES = get_2letters_languages()

    def update_index(self, resource: ResourceBase, jsonschema: dict, jsoninstance: dict):

        ml_fields = {}
        nonml_fields = {}

        involved_fields = {field for fields in settings.METADATA_INDEXES.values() for field in fields}

        # first loop: gather values
        for fieldname in involved_fields:
            if is_multilang(fieldname, jsonschema):
                ml_fields[fieldname] = {}
                for lang, loc_field_name in get_multilang_field_names(fieldname):
                    ml_fields[fieldname][lang] = jsoninstance.get(loc_field_name, "")
            else:
                nonml_fields[fieldname] = jsoninstance.get(fieldname, None)

        # 2nd loop: fill in missing title entries
        # i.e. if a title is missing the content for a given lang, it will be filled with the content
        # of every other lang to allow the entry to be discoverable.
        if "title" in involved_fields and "title" in ml_fields:
            if any(not content for content in ml_fields["title"].values()):
                merged = " ".join([content for content in ml_fields["title"].values() if content])
                merged = f"{merged} {jsoninstance.get('title', '')}"  # also add plain title

                for lang,content in ml_fields["title"].items():
                    if not content:
                        logger.debug(f"Filling in title for empty lang {lang}")
                        ml_fields["title"][lang] = merged

        # 3rd loop: create indexes
        for index_name, index_fields in settings.METADATA_INDEXES:

            if all(field in nonml_fields for field in index_fields):
                # the index is not localized
                index_text = " ".join((nonml_fields[f] for f in index_fields))
                vector = SearchVector(index_text)  ## TODO: do we need a language config? default lang? "simple"?

                ResourceIndex.objects.update_or_create(
                    resource=resource,
                    lang=None,
                    name=index_name,
                    defaults={"vector": vector}
                )
                # remove all localized indexes if any
                ResourceIndex.objects.filter(
                    resource=resource,
                    lang__is_null=False,
                    name=index_name,
                ).delete()

            else:  # some indexed fields are multilang
                pass
                # TODO
            pass

            # TODO


index_manager = IndexManager()