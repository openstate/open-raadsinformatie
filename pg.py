import pymysql.cursors
from pprint import pprint
from datetime import date, datetime
import json

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='[PASSWORD HERE]',
                             db='pol_new',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.SSCursor)

print('Started')

statement = """SELECT sd.identifier, sd.uitslag, sd._vergaderjaar, sd.url, sd.handopsteken, kl.identifier, id.indiener, sd.nr, sd._issuedate, sd._titel, sd._tekst, sd.jaar
FROM `new_stemdetails` as sd
LEFT JOIN `new_indieners` as id ON sd.identifier = id.identifier
LEFT JOIN `new_kamerleden` as kl ON id.indiener = kl.naam
ORDER BY `sd`.`identifier` ASC, id.Volgorde ASC"""
cursor = connection.cursor()
cursor.execute(statement)
print("first query done")

stemmingen = dict()

prev_id = None
for row in cursor:
    if prev_id == row[0]:
        if row[6]:
            stemming['indieners'].append((row[5], row[6],))
        continue
    else:
        if prev_id:
            stemmingen[prev_id] = stemming

    stemming = {
        "identifier": row[0],
        "uitslag": bool(row[1]),
        "jaar": row[2],
        "url": row[3],
        "handopsteken": bool(row[4]),
        # "foutkamerlid": row[11]
    }

    if row[6]:
        stemming['indieners'] = [(row[5], row[6],)]

    if row[7]:
        stemming['plenair_id'] = '{}P{:>05}'.format(row[11], row[7])
        stemming['issuedate'] = row[8]
        stemming['titel'] = row[9]
        stemming['tekst'] = row[10]

    prev_id = stemming['identifier']

# Last one when loop ended
stemmingen[prev_id] = stemming
del stemming


statement = """SELECT sa.*, bijzonderheid
FROM `new_stemaantal` as sa
LEFT JOIN `new_stembijzonderheden` as sv ON sa.identifier = sv.identifier and sa.partij = sv.stemmer and sv.bijzonderheid = 1
ORDER BY sa.`identifier` ASC"""
cursor = connection.cursor()
cursor.execute(statement)
print("second query done")

votes = dict()
for row in cursor:
    vote = {
        "partij": row[1],
        "aantal": row[3],
    }
    if row[2]:
        vote['kamerlid'] = row[2]

    if row[5] == 1:
        vote['vergissing'] = True

    if row[4] == 1:
        decision = 'voor'
    elif row[4] == 0:
        decision = 'tegen'
    elif row[4] == -1:
        decision = 'afwezig'
    elif row[4] == -2:
        decision = 'fout'
        raise Exception('Fout aanwezig in decision')
    else:
        raise Exception('Niet bestaande decision')

    try:
        stemmingen[row[0]]['votes'][decision].append(vote)
    except KeyError:
        if not 'votes' in stemmingen[row[0]]:
            stemmingen[row[0]]['votes'] = dict()

        stemmingen[row[0]]['votes'][decision] = [vote]


statement = """
SELECT ks.identifier, ks.idkamerstuk, ba.Hoofd, ba.Sub
FROM kamerstuk AS ks
INNER JOIN kst_beleidsagenda AS kba ON ks.idkamerstuk = kba.id_kamerstuk
LEFT JOIN beleidsagenda AS ba ON kba.id_beleidsagenda = ba.idBeleidsagenda"""
cursor = connection.cursor()
cursor.execute(statement)
print("third query done")

for row in cursor:
    identifier = row[0][4:]

    if identifier not in stemmingen:
        continue

    try:
        stemmingen[identifier]['beleidsagenda'][row[2]].append(row[3])
    except KeyError:
        stemmingen[identifier]['beleidsagenda'] = {row[2]: [row[3]]}


statement = """
SELECT ks.identifier, ks.idkamerstuk, ds.dossiernr, ds.dossiertitel
FROM kamerstuk AS ks
INNER JOIN kst_dossier AS kds ON ks.idkamerstuk = kds.idkst
LEFT JOIN dossier AS ds ON kds.iddossier = ds.iddossier"""
cursor = connection.cursor()
cursor.execute(statement)
print("fourth query done")

for row in cursor:
    identifier = row[0][4:]

    if identifier not in stemmingen:
        continue

    try:
        stemmingen[identifier]['dossiers'].append({'dossiernr': row[2], 'dossier': row[3]})
    except KeyError:
        stemmingen[identifier]['dossiers'] = [{'dossiernr': row[2], 'dossier': row[3]}]


# statement = """
# SELECT ks.identifier, ks.idkamerstuk, op.onderwerp, GROUP_CONCAT(woord) AS woorden
# FROM `kamerstuk` as ks
# LEFT JOIN `onderwerp_motie` as os ON ks.idkamerstuk = os.idmotie
# LEFT JOIN `onderwerpen` as op ON os.idonderwerp = op.idonderwerp
# LEFT JOIN `onderwerp_woorden` as ow ON ow.idonderwerp = op.idonderwerp
# WHERE ow.idonderwerp IS NOT NULL
# GROUP BY ks.idkamerstuk, os.idonderwerp
# ORDER BY `ks`.`idkamerstuk` ASC"""
# cursor = connection.cursor()
# cursor.execute(statement)
# print("fifth query done")
#
# for row in cursor:
#     identifier = row[0][4:]
#
#     if identifier not in stemmingen:
#         continue
#
#     woorden = row[3].split(',')
#
#     try:
#         stemmingen[identifier]['onderwerpen'][row[2]] = woorden
#     except KeyError:
#         stemmingen[identifier]['onderwerpen'] = {row[2]: woorden}


print('Serialize')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


f = open('pg_motions.json', 'w')
json.dump([x for x in stemmingen.values()], f, default=json_serial)

print('Done!')
