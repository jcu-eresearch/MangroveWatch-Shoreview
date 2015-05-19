import csv
import json


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

with open('MangroveAnnotations.csv', 'rb') as csvfile:
    reader = csv.reader(x.replace('\0', '') for x in csvfile)

    json_data = []

    for row_index, row in enumerate(reader):

        category = ""

        for index, col in enumerate(row):

            if col == "":
                #pk = row_index + 1
                pk = None
                model = "projects.AnnotationCodes"
                code = category
                category = rreplace(category, ":"+row[index-1], "", 1)
                name = row[index-1]



                fields = {"category_name": category, "caab_code": code, "cpc_code": "", "point_colour": "", "code_name": name, "description": "", "parent": None, "annotation_scheme": ["Mangrove Watch Classification", "1.0"]}
                item = {"pk": pk, "model": "projects.AnnotationCodes", "fields": fields}
                json_data.append(item)

                #print str(pk) + " - " + category + " - " + name + " - " + code

                break

            if category == "":
                category = col
            else:
                category = category + ":" + col

    print json.dumps(json_data)