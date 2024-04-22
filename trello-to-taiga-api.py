import json
import os
import logging

from datetime import datetime
from taiga import TaigaAPI

LOG = logging.getLogger(__name__)

#
# Setup environment variables
#
host = os.getenv('TAIGA_HOST')
username = os.getenv('TAIGA_USERNAME')
password = os.getenv('TAIGA_PASSWORD')
project_slug = os.getenv('TAIGA_PROJECT_SLUG')

required_env_vars = [
    'TAIGA_HOST', 'TAIGA_USERNAME', 'TAIGA_PASSWORD', 'TAIGA_PROJECT_SLUG'
]
for var in required_env_vars:
    if os.getenv(var) is None:
        raise ValueError(f"Required environment variable '{var}' is not set")

api = TaigaAPI(host=host)
api.auth(
    username=username,
    password=password
)

project = None
projects = api.projects.list()
for p in projects:
    if p.slug == project_slug:
        project = p
        break
assert project is not None


with open('trainings_trello.json') as f:
    data = json.load(f)

#
# Get all cards
#
response_cards = data['cards']
cards_dict = {}
for card in response_cards:
    cards_dict[card['name']] = card

#
# Get all custom fields and duration options
#
custom_fields_dict = {}
duration_dict = {}
custom_fields = data['customFields']
for custom_field in custom_fields:
    custom_fields_dict[custom_field['name']] = custom_field
    if custom_field['name'] == 'Exact Address' and 'options' in custom_field:
        for option in custom_field['options']:
            duration_dict[option['id']] = option['value']['text']
#
# Get custom fields id to name dict
#
custom_fields_id_to_name_dict = {}
for custom_field in custom_fields:
    custom_fields_id_to_name_dict[custom_field['id']] = custom_field['name']
#
# Get trainer options
#
trainer_options = custom_fields_dict['Trainer']['options']
trainer_dict = {}
for option in trainer_options:
    trainer_dict[option['id']] = option['value']['text']
#
# Get type options
#
type_options = custom_fields_dict['Type']['options']
type_dict = {}
for option in type_options:
    type_dict[option['id']] = option['value']['text']

#
# Get custom fields items for each card with their values
#
custom_field_dicts = {
    'Trainer': trainer_dict,
    'Type': type_dict,
    'Exact Address': duration_dict
}
custom_fields_items_dict = {}
for card_name in cards_dict.keys():
    custom_field_items = cards_dict[card_name]['customFieldItems']
    if custom_field_items:
        for item in custom_field_items:
            field_name = custom_fields_id_to_name_dict.get(item['idCustomField'])
            if field_name:
                if card_name not in custom_fields_items_dict:
                    custom_fields_items_dict[card_name] = {}
                if item['value']:
                    if 'date' in item['value']:
                        date_string = item['value']['date']
                        date_time = datetime.fromisoformat(date_string)
                        date_string = date_time.strftime('%d %b %Y')
                        custom_fields_items_dict[card_name][field_name] = date_string
                    else:
                        custom_fields_items_dict[card_name][field_name] = item['value'].get('text', '')
                else:
                    id_value = item.get('idValue')
                    if id_value:
                        field_dict = custom_field_dicts.get(field_name)
                        if field_dict:
                            name = field_dict.get(id_value)
                            if name:
                                custom_fields_items_dict[card_name][field_name] = name
                if field_name == 'Exact Address':
                    duration_value = duration_dict.get(item['idValue'], '')
                    if duration_value:
                        custom_fields_items_dict[card_name]['Duration'] = duration_value
                        continue

#
# Get all custom attributes of user stories in the project
#
custom_attributes_ids = {}
custom_attributes = api.user_story_attributes.list(project=project.id)
for custom in custom_attributes:
    custom_attributes_ids[custom.name] = custom.id

#
# Get all user stories and update the custom fields with the values from the cards
#
dropdown_option_fields = ['Trainer', 'Type', 'Duration']
for card_name in cards_dict.keys():
    custom_field_items = custom_fields_items_dict.get(card_name, {})

    user_stories = api.user_stories.list(project=project.id)
    matching_user_story = None
    for user_story in user_stories:
        if user_story.subject == card_name:
            matching_user_story = user_story
            break

    if matching_user_story:
        for field_name, field_value in custom_field_items.items():
            attribute_id = custom_attributes_ids.get(field_name)
            if attribute_id:
                if field_name in dropdown_option_fields:
                    custom_attribute = None
                    for ca in custom_attributes:
                        if ca.id == attribute_id:
                            custom_attribute = ca
                            break
                    if custom_attribute:
                        possible_values = custom_attribute.extra
                        if field_value not in possible_values:
                            LOG.warning(f"Field value '{field_value}' for custom field '{field_name}' in card '{card_name}' is not valid. Skipping this field.")
                            continue
                try:
                    matching_user_story.set_attribute(attribute_id, field_value)
                except Exception as e:
                    LOG.error(f"Error setting attribute '{field_name}' for user story '{card_name}': {e}")
