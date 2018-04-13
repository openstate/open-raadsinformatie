from collections import MutableMapping
from datetime import datetime
from hashlib import sha1
import json

from ocd_backend.utils import json_encoder
from ocd_backend.exceptions import (UnableToGenerateObjectId,
                                    FieldNotAvailable)
from ocd_backend.items import BaseItem


class PopoloBaseItem(BaseItem):
    pass


class PersonItem(PopoloBaseItem):
    # Allowed key-value pairs for the document inserted in the 'combined index'
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'name': unicode,
        'other_names': list,
        'identifiers': list,
        'family_name': unicode,
        'given_name': unicode,
        'additional_name': unicode,
        'honorific_prefix': unicode,
        'honorific_suffix': unicode,
        'patronymic_name': unicode,
        'sort_name': unicode,
        'email': unicode,
        'gender': unicode,
        'birth_date': datetime,
        'death_date': datetime,
        'image': unicode,
        'summary': unicode,
        'biography': unicode,
        'national_identity': unicode,
        'contact_details': list,
        'links': list,
        'memberships': list,
        'created_at': datetime,
        'updated_at': datetime,
        'sources': list,
        'media_urls': list,
    }


class OrganisationItem(PopoloBaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'name': unicode,
        'other_names': list,
        'identifiers': list,
        'classification': unicode,
        'parent_id': unicode,
        'area_id': unicode,
        'area': dict,
        'abstract': unicode,
        'description': unicode,
        'founding_date': datetime,
        'dissolution_date': datetime,
        'image': unicode,
        'contact_details': list,
        'links': list,
        'memberships': list,
        'created_at': datetime,
        'updated_at': datetime,
        'sources': list,
        'media_urls': list,
    }


class MembershipItem(PopoloBaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'label': unicode,
        'role': unicode,
        'member': dict,
        'person_id': unicode,
        'person': dict,
        'organization_id': unicode,
        'organization': dict,
        'post_id': unicode,
        'post': dict,
        'on_behalf_of_id': unicode,
        'on_behalf_of': dict,
        'area_id': unicode,
        'area': dict,
        'start_date': datetime,
        'end_date': datetime,
        'contact_details': list,
        'links': list,
        'created_at': datetime,
        'updated_at': datetime,
        'sources': list,
        'media_urls': list        
    }


class EventItem(PopoloBaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'name': unicode,
        'description': unicode,
        'start_date': datetime,
        'end_date': datetime,
        'date_granularity': int,
        'status': unicode,
        'location': unicode,
        'identifiers': list,
        'classification': unicode,
        'organization_id': unicode,
        'organization': dict,
        'attendees': list,
        'parent_id': unicode,
        'sources': list,
        'children': list,
        'media_urls': list,
    }


class MotionItem(PopoloBaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'name': unicode,
        'organization_id': unicode,
        'organization': dict,
        'legislative_session_id': unicode,
        'legislative_session': dict,
        'creator_id': unicode,
        'creator': dict,
        'text': unicode,
        'identifier': unicode,  # unsure
        'classification': unicode,
        'date': datetime,
        'start_date': datetime,
        'end_date': datetime,
        'requirement': unicode,
        'result': unicode,
        'vote_events': list,
        'sources': list,
        'media_urls': list,
    }


class VotingEventItem(PopoloBaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'name': unicode,
        'organization_id': unicode,
        'organization': dict,
        'legislative_session_id': unicode,
        'legislative_session': dict,
        'text': unicode,
        'identifier': unicode,  # unsure
        'classification': unicode,
        'motion_id': unicode,
        'motion': dict,
        'start_date': datetime,
        'end_date': datetime,
        'result': unicode,
        'counts': list,
        'votes': list,
        'sources': list,
        'media_urls': list,
    }
