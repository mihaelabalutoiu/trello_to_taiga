import json

template_path = 'template.json'
trello_export_path = 'trainings_trello.json'
taiga_import_path = "import.json"

default_email = "info@cloudbasesolutions.com"
with open(template_path) as f:
    data = json.load(f)

with open(trello_export_path) as f:
    trello_data = json.load(f)

name = trello_data["name"]
desc = trello_data["desc"]

if trello_data["desc"] == "":
    desc = "trainings-by-cloudbase-solutions"

data["name"] = name
data["slug"] = name.lower().replace(" ", "-")
data["description"] = desc
data["watchers"] = [default_email]

lists = {}
data["us_statuses"] = []

for i, l in enumerate(trello_data["lists"], 1):
    name = l["name"]
    lists[l["id"]] = name

    data["us_statuses"].append({
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "order": i,
        "is_closed": False,
        "is_archived": False,
        "color": "#70728F",
        "wip_limit": None
    })

data["default_us_status"] = data["us_statuses"][0]["name"]

for i, card in enumerate(trello_data["cards"], 1):
    name = card["name"]
    desc = card["desc"]
    list_id = card["idList"]
    last_activity = card["dateLastActivity"]
    closed = card["closed"]
    if card["desc"] == "":
        desc = None
    data["user_stories"].append({
      "watchers": [],
      "attachments": [],
      "history": [],
      "custom_attributes_values": {},
      "role_points": [],
      "owner": default_email,
      "assigned_to": default_email,
      "assigned_users": [default_email],
      "status": lists[list_id],
      "swimlane": None,
      "milestone": None,
      "modified_date": last_activity,
      "created_date": last_activity,
      "finish_date": None,
      "generated_from_issue": None,
      "generated_from_task": None,
      "from_task_ref": None,
      "ref": i,
      "is_closed": closed,
      "backlog_order": 1711984560338393,
      "sprint_order": 1711984560338443,
      "kanban_order": 1,
      "subject": name,
      "description": desc,
      "client_requirement": False,
      "team_requirement": False,
      "external_reference": None,
      "tribe_gig": None,
      "version": 5,
      "blocked_note": "",
      "is_blocked": False,
      "tags": [],
      "due_date": None,
      "due_date_reason": ""
    })

#
# Create custom fields for user stories
#
for c, customField in enumerate(trello_data["customFields"], 1):
    name = customField["name"]
    type = customField["type"]
    if customField["type"] == "list":
        type = "dropdown"

    # We need unique names
    names = [i['name'] for i in data['userstorycustomattributes']]
    if customField["name"] in names:
        name = customField["name"] + str(c)

    data['userstorycustomattributes'].append({
        "name": name,
        "description": name,
        "type": type,
        "order": c,
    })

with open(taiga_import_path, "w") as f:
    json.dump(data, f, indent=2)
