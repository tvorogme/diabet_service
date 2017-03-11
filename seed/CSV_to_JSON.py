import csv
d = {}
with open('food.csv', 'r') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        name = str(row[0]).replace(' ', '')
        d[name] = {}
        d[name]['name'] = str(row[1])
        d[name]['cals'] = float(str(row[2]).replace(',', '.'))
        d[name]['prot'] = float(str(row[3]).replace(',', '.'))
        d[name]['fat'] = float(str(row[4]).replace(',', '.'))
        d[name]['ugl'] = float(str(row[5]).replace(',', '.'))
        d[name]['xe'] = float(str(row[6]).replace(',', '.'))
        d[name]['color'] = str(row[7])
        r = d[name]

import json
with open('food.json', 'w') as file:
    file.write(json.dumps(d))