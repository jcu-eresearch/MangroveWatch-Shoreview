import csv
import json

"""
file = open('catami_classification_tree.json')

json_content = json.loads(file.read())


for count, item in enumerate(json_content):
    print json_content[count]['fields']['code_name'], ",", json_content[count]['fields']['cpc_code'], ",", json_content[count]['fields']['caab_code']
"""


items = []

scheme = [dict(pk=None, model="projects.AnnotationSchemes", fields=dict(
    owner=None, name="CATAMI Classification", version="1.3"
))]

# open up the csv file and convert the rows into dicts conforming to the AnnotationCodes model
with open("catami-class-1.3.csv", 'rb') as csvfile:
    scheme_reader = csv.reader(x.replace('\0', '') for x in csvfile)

    for index, row in enumerate(scheme_reader):
        parent = [["CATAMI Classification","1.3"], row[2]]

        if row[2] == "":
            parent = None

        fields = dict(
                    caab_code=row[0],
                    code_name=row[1],
                    parent=parent,
                    cpc_code=row[3].replace(" ", ""),
                    point_colour=row[4],
                    description="No description",
                    annotation_scheme=[
                        "CATAMI Classification",
                        "1.3"
                      ]
        )

        item = dict(pk=None,
                    model="projects.AnnotationCodes",
                    fields=fields)

        items.append(item)

#reorder the items
ordered_list = []
def find_children(full_list, parent_code):

    global ordered_list
    children = []

    for item in full_list:
        #print item["fields"]["parent"], parent_code
        if parent_code == item["fields"]["parent"]:
            children.append(item)
        elif item["fields"]["parent"] != None:
            if parent_code == item["fields"]["parent"][1]:
                children.append(item)

    ordered_list = ordered_list + children

    for child in children:
        find_children(full_list, child["fields"]["caab_code"])


find_children(items, None)

print json.dumps(scheme + ordered_list)