import datetime
import json

template_path = 'template.json'
trello_export_path = 'trainings_trello.json'
taiga_import_path = "import.json"

default_email = "info@cloudbasesolutions.com"
with open(template_path) as f:
    data = json.load(f)

with open(trello_export_path) as f:
    trello_data = json.load(f)

name = "Trainings By Cloudbase Solutions"
desc = trello_data["desc"]

if trello_data["desc"] == "":
    desc = "Imported from Trello"

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

#
# Append new values to the `roles` field
#
ux_role = {
    "name": "UX",
    "slug": "ux",
    "order": 10,
    "computable": True,
    "permissions": data["roles"][0]["permissions"]
}

design_role = {
    "name": "Design",
    "slug": "design",
    "order": 20,
    "computable": True,
    "permissions": data["roles"][0]["permissions"]
}

front_role = {
    "name": "Front",
    "slug": "front",
    "order": 30,
    "computable": True,
    "permissions": data["roles"][0]["permissions"]
}

back_role = {
    "name": "Back",
    "slug": "back",
    "order": 40,
    "computable": True,
    "permissions": data["roles"][0]["permissions"]
}

stakeholder_role = {
    "name": "Stakeholder",
    "slug": "stakeholder",
    "order": 60,
    "computable": False,
    "permissions": [
        "add_issue",
        "modify_issue",
        "delete_issue",
        "view_issues",
        "view_milestones",
        "view_project",
        "view_tasks",
        "view_us",
        "modify_wiki_page",
        "view_wiki_pages",
        "add_wiki_link",
        "delete_wiki_link",
        "view_wiki_links",
        "view_epics",
        "comment_epic",
        "comment_us",
        "comment_task",
        "comment_issue",
        "comment_wiki_page"
    ]
}

trello_role = {
    "name": "Trello",
    "slug": "trello",
    "order": 70,
    "computable": False,
    "permissions": data["roles"][0]["permissions"]
}

data["roles"].extend([
    ux_role, design_role, front_role, back_role, stakeholder_role,
    trello_role
])
data["roles"] = sorted(data["roles"], key=lambda x: x["order"])

data["default_us_status"] = data["us_statuses"][0]["name"]

for i, card in enumerate(trello_data["cards"], 1):
    name = card["name"]
    if name.lower() == "test":
        continue
    desc = card["desc"]
    list_id = card["idList"]
    last_activity = card["dateLastActivity"]
    closed = card["closed"]
    if card["desc"] == "":
        desc = None
    tags = []
    for label in card["labels"]:
        # We need to remove the spaces from the labels
        if label["name"].strip():
            tags.append(label["name"].lower())

# Add the attachments
    attachments = []
    for attachment in card["attachments"]:
        attachments.append({
            "owner": default_email,
            "attached_file": {
                "data": "",
                "name": attachment["fileName"]
            },
            "created_date": attachment["date"],
            "modified_date": attachment["date"],
            "description": "",
            "is_deprecated": False,
            "name": attachment["name"],
            "order": i,
            "sha1": "",
            "size": attachment["bytes"],
        })

    data["user_stories"].append({
      "watchers": [],
      "attachments": attachments,
      "history": [],
      "custom_attributes_values": {},
      "role_points": [],
      "owner": default_email,
      "assigned_to": None,
      "assigned_users": [],
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
      "tags": tags,
      "due_date": None,
      "due_date_reason": ""
    })

#
# Create custom fields for user stories
#
description_map = {
    "Type": "Training Type",
    "Location": "Training Location: \"Remote\" or full address",
    "Trainer": "The trainer that will deliver the training",
    "Start Date": "Training start date",
    "Start Time": "Training start time (local time)",
    "Timezone": "Customer local timezone",
    "Duration": "Training duration",
    "Contact": "Main client contact person",
    "Attendees": "List of attendees (name and email address)"
}

multiline_names = {"Location", "Attendees"}

name_map = {
    "Exact Address": ["Duration", "Attendees"],
}

seen = set()
for c, customField in enumerate(trello_data["customFields"], 1):
    name = customField["name"]
    type = customField["type"]
    if type == "list":
        type = "dropdown"

    if name in name_map and name_map[name]:
        new_name = name_map[name].pop(0)
        if new_name not in seen:
            name = new_name
            seen.add(new_name)

    if name in multiline_names:
        type = "multiline"

    # Get the current date and time in the required format
    current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000")

    data['userstorycustomattributes'].append({
        "name": name,
        "description": description_map.get(name, name),
        "type": type,
        "order": c,
        "created_date": current_date,
        "modified_date": current_date
    })

#
# Append new values to the `points` field
#
new_values = [
    {
        "name": "?",
        "order": 1,
        "value": None
    },
    {
        "name": "0",
        "order": 2,
        "value": 0.0
    },
    {
        "name": "1/2",
        "order": 3,
        "value": 0.5
    },
    {
        "name": "1",
        "order": 4,
        "value": 1.0
    },
    {
        "name": "2",
        "order": 5,
        "value": 2.0
    },
    {
        "name": "3",
        "order": 6,
        "value": 3.0
    },
    {
        "name": "5",
        "order": 7,
        "value": 5.0
    },
    {
        "name": "8",
        "order": 8,
        "value": 8.0
    },
    {
        "name": "10",
        "order": 9,
        "value": 10.0
    },
    {
        "name": "13",
        "order": 10,
        "value": 13.0
    },
    {
        "name": "20",
        "order": 11,
        "value": 20.0
    }
]
data["points"].extend(new_values)
data["points"] = sorted(data["points"], key=lambda x: x["order"])

if data['default_points'] == '40':
    data['default_points'] = '?'
#
# Append new values to the `epic_statuses` field
#
new_values = [
    {
        "name": "New",
        "slug": "new",
        "order": 1,
        "is_closed": False,
        "color": "#70728F"
    },
    {
        "name": "Ready",
        "slug": "ready",
        "order": 2,
        "is_closed": False,
        "color": "#E44057"
    },
    {
        "name": "In progress",
        "slug": "in-progress",
        "order": 3,
        "is_closed": False,
        "color": "#E47C40"
    },
    {
        "name": "Ready for test",
        "slug": "ready-for-test",
        "order": 4,
        "is_closed": False,
        "color": "#E4CE40"
    }
]
data['epic_statuses'].extend(new_values)
data['epic_statuses'] = sorted(data['epic_statuses'], key=lambda x: x['order'])

if data['default_epic_status'] == 'Done':
    data['default_epic_status'] = 'New'

#
# Append new values to the `us_duedates` field
#
new_values = [
    {
        "name": "Due soon",
        "order": 2,
        "by_default": False,
        "color": "#ff9900",
        "days_to_due": 14
    },
    {
        "name": "Past due",
        "order": 3,
        "by_default": False,
        "color": "#E44057",
        "days_to_due": 0
    }
]
data["us_duedates"].extend(new_values)

#
# Append new values to the `task_statuses` field
#
for task_status in data['task_statuses']:
    if task_status['name'] == 'Needs Info':
        task_status['name'] = 'Incomplete'
        task_status['slug'] = 'incomplete'
        task_status['order'] = 1
        task_status['is_closed'] = False
        task_status['color'] = '#ff8a84'

new_task_status = {
    "name": "Complete",
    "slug": "complete",
    "order": 2,
    "is_closed": True,
    "color": "#669900"
}
data['task_statuses'].append(new_task_status)

if data['default_task_status'] == 'Needs Info':
    data['default_task_status'] = 'Incomplete'

#
# Append new values to the `task_duedates` field
#
new_values = [
    {
        "name": "Due soon",
        "order": 2,
        "by_default": False,
        "color": "#ff9900",
        "days_to_due": 14
    },
    {
        "name": "Past due",
        "order": 3,
        "by_default": False,
        "color": "#E44057",
        "days_to_due": 0
    }
]
data["task_duedates"].extend(new_values)

#
# Append new values to the `issue_types` field
#
new_values = [
    {
        "name": "Bug",
        "order": 1,
        "color": "#E44057"
    },
    {
        "name": "Question",
        "order": 2,
        "color": "#5178D3"
    }
]

data["issue_types"].extend(new_values)
data["issue_types"] = sorted(data["issue_types"], key=lambda x: x["order"])

if data['default_issue_type'] == 'Enhancement':
    data['default_issue_type'] = 'Bug'

#
# Append new values to the `issue_statuses` field
#
new_values = [
    {
        "name": "New",
        "slug": "new",
        "order": 1,
        "is_closed": False,
        "color": "#70728F"
    },
    {
        "name": "In progress",
        "slug": "in-progress",
        "order": 2,
        "is_closed": False,
        "color": "#40A8E4"
    },
    {
        "name": "Ready for test",
        "slug": "ready-for-test",
        "order": 3,
        "is_closed": False,
        "color": "#E47C40"
    },
    {
        "name": "Closed",
        "slug": "closed",
        "order": 4,
        "is_closed": True,
        "color": "#A8E440"
    },
    {
        "name": "Needs Info",
        "slug": "needs-info",
        "order": 5,
        "is_closed": False,
        "color": "#E44057"
    },
    {
        "name": "Rejected",
        "slug": "rejected",
        "order": 6,
        "is_closed": True,
        "color": "#A9AABC"
    }
]
data["issue_statuses"].extend(new_values)
data["issue_statuses"] = sorted(
    data["issue_statuses"], key=lambda x: x["order"])

if data['default_issue_status'] == 'Postponed':
    data['default_issue_status'] = 'New'

#
# Append new values to the `issue_duedates` field
#
new_values = [
    {
        "name": "Due soon",
        "order": 2,
        "by_default": False,
        "color": "#ff9900",
        "days_to_due": 14
    },
    {
        "name": "Past due",
        "order": 3,
        "by_default": False,
        "color": "#E44057",
        "days_to_due": 0
    }
]
data["issue_duedates"].extend(new_values)

#
# Append new values to the `priorities` field
#
new_values = [
    {
        "name": "Low",
        "order": 1,
        "color": "#A9AABC"
    },
    {
        "name": "Normal",
        "order": 3,
        "color": "#A8E440"
    }
]
data["priorities"].extend(new_values)
data["priorities"] = sorted(data["priorities"], key=lambda x: x["order"])

if data['default_priority'] == 'High':
    data['default_priority'] = 'Normal'

#
# Append new values to the `severities` field
#
new_values = [
    {
        "name": "Wishlist",
        "order": 1,
        "color": "#70728F"
    },
    {
        "name": "Minor",
        "order": 2,
        "color": "#40E47C"
    },
    {
        "name": "Normal",
        "order": 3,
        "color": "#A8E440"
    },
    {
        "name": "Important",
        "order": 4,
        "color": "#E4CE40"
    }
]
data["severities"].extend(new_values)
data["severities"] = sorted(data["severities"], key=lambda x: x["order"])

if data['default_severity'] == 'Critical':
    data['default_severity'] = 'Normal'

#
# Create tasks from the checklists
#
task_template = {
    "watchers": [],
    "attachments": [],
    "history": [],
    "custom_attributes_values": {},
    "owner": None,
    "status": None,
    "user_story": 145,
    "milestone": None,
    "assigned_to": None,
    "modified_date": None,
    "created_date": None,
    "finished_date": None,
    "ref": None,
    "subject": None,
    "us_order": None,
    "taskboard_order": None,
    "description": "",
    "is_iocaine": False,
    "external_reference": None,
    "version": 1,
    "blocked_note": "",
    "is_blocked": False,
    "tags": [],
    "due_date": None,
    "due_date_reason": ""
}

ref_counter = 160
for checklist in trello_data['checklists']:
    for check_item in checklist['checkItems']:
        task = task_template.copy()
        task['status'] = 'Complete'
        if check_item['state'] == 'complete':
            task['status'] = 'Complete'
        else:
            task['status'] = 'Incomplete'
        task['subject'] = check_item['name']
        current_time = datetime.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S+0000")
        task['modified_date'] = current_time
        task['created_date'] = current_time
        task['finished_date'] = current_time
        task['us_order'] = task['taskboard_order'] = check_item['pos']
        task['ref'] = ref_counter
        ref_counter += 1
        data['tasks'].append(task)

#
# Append labels to the tags_color field
#
color_map = {
    "green": "#008000",
    "sky": "sky",
    "black": "#000000",
    "orange": "#ffa500",
    "red": "#ff0000",
    "yellow": "#ffff00",
    "blue": "#0000ff",
    "lime": "#00ff00",
    "purple": "#800080",
    "pink": "ffc0cb",
    "null": None
}
new_tags_colors = []
for label in trello_data["labels"]:
    name, color = label["name"], label["color"]
    if color == "purple" and name == "":
        name = "purple"
    color_hex = color_map.get(color, None)
    new_tags_colors.append([name.lower(), color_hex])

data["tags_colors"] = new_tags_colors

with open(taiga_import_path, "w") as f:
    json.dump(data, f, indent=2)
