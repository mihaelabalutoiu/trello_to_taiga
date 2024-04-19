import requests
import os
import logging

from datetime import datetime
from requests_oauthlib import OAuth1
from taiga import TaigaAPI
from taiga import exceptions as exc

LOG = logging.getLogger(__name__)

#
# Setup environment variables
#
api_key = os.getenv('TRELLO_API_KEY')
token = os.getenv('TRELLO_TOKEN')
board_id = os.getenv('TRELLO_BOARD_ID')
api_secret = os.getenv('TRELLO_API_SECRET')

host = os.getenv('TAIGA_HOST')
username = os.getenv('TAIGA_USERNAME')
password = os.getenv('TAIGA_PASSWORD')
project_slug = os.getenv('TAIGA_PROJECT_SLUG')

required_env_vars = [
    'TRELLO_API_KEY', 'TRELLO_API_SECRET', 'TRELLO_TOKEN', 'TRELLO_BOARD_ID',
    'TAIGA_HOST', 'TAIGA_USERNAME', 'TAIGA_PASSWORD', 'TAIGA_PROJECT_SLUG'
]
for var in required_env_vars:
    if os.getenv(var) is None:
        raise ValueError(f"Required environment variable '{var}' is not set")


class TrelloClient:
    def __init__(self, api_key, api_secret, token):
        self.api_key = api_key
        self.api_secret = api_secret
        self.token = token
        self.oauth = OAuth1(
            client_key=self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.token
        )

    def _validate_response(self, response):
        if response.status_code == 400:
            raise exc.WrongArguments(
                (f"Invalid Request:{response.text} at {response.url}"))
        if response.status_code == 401:
            raise exc.AuthenticationFailed(
                (f"Unauthorized: {response.text} at {response.url}"))
        if response.status_code == 403:
            raise exc.PermissionDenied(
                (f"Unauthorized: {response.text} at {response.url}"))
        if response.status_code == 404:
            raise exc.NotFound(
                (f"Resource Unavailable: {response.text} at {response.url}"))
        if response.status_code != 200:
            raise exc.WrongArguments(
                (f"Resource Unavailable: {response.text} at {response.url}"))

    def get(self, uri_path, query_params=None):
        headers = {'Accept': 'application/json'}

        if query_params is None:
            query_params = {}

        if uri_path[0] == '/':
            uri_path = uri_path[1:]
        url = f'https://api.trello.com/1/{uri_path}'

        response = requests.get(
            url, params=query_params, headers=headers, auth=self.oauth)
        self._validate_response(response)
        return response.json()

    def download(self, url):
        response = requests.get(url, auth=self.oauth)
        self._validate_response(response)
        return response.content


client = TrelloClient(
    api_key=api_key,
    api_secret=api_secret,
    token=token
)

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

#
# Get all cards
#
response_cards = client.get(f"boards/{board_id}/cards")
cards_dict = {}
for card in response_cards:
    cards_dict[card['name']] = card

#
# Get all custom fields
#
custom_fields_dict = {}
response_custom_fields = client.get(f"boards/{board_id}/customFields")
for custom_field in response_custom_fields:
    custom_fields_dict[custom_field['name']] = custom_field

#
# Get custom fields id to name dict
#
custom_fields_id_to_name_dict = {}
for custom_field in response_custom_fields:
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
# Get duration options
#
duration_options = custom_fields_dict['Duration']['options']
duration_dict = {}
for option in duration_options:
    duration_dict[option['id']] = option['value']['text']

#
# Get custom fields items for each card with their values
#
custom_field_dicts = {
    custom_fields_dict['Trainer']['id']: trainer_dict,
    custom_fields_dict['Type']['id']: type_dict,
    custom_fields_dict['Duration']['id']: duration_dict
}
custom_fields_items_dict = {}
for card_name in cards_dict.keys():
    card_id = cards_dict[card_name]['id']
    response_custom_field_items = client.get(f"cards/{card_id}/customFieldItems")
    if response_custom_field_items:
        for item in response_custom_field_items:
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
                        custom_fields_items_dict[card_name][field_name] = item[
                            'value'].get('text', '')
                else:
                    id_value = item.get('idValue')
                    if id_value:
                        field_dict = custom_field_dicts.get(
                            item['idCustomField'])
                        if field_dict:
                            name = field_dict.get(id_value)
                            if name:
                                custom_fields_items_dict[card_name][field_name] = name
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
                            LOG.warning(f"Field value '{field_value}' for custom field '{field_name}' in card '{card_name}' is not valid, skipping")
                            continue
                try:
                    matching_user_story.set_attribute(attribute_id, field_value)
                except exc.TaigaException as e:
                    LOG.error(f"Error setting attribute: {e}")
