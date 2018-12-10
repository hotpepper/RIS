import os


# add ignore file
f = open('.gitignore', 'w')
exts = [
    '*.idea',
    '*.pyc',
    '*.mdb',
    '*.csv',
    '*.xls',
    '*.xlsx',
    '*.shp',
    '*.cpg',
    '*.dbf',
    '*.prj',
    '*.sbn',
    '*.sbx',
    '*.xml',
    '*.zip']
for i in exts:
    f.write(i)
f.close()

folders = [
    'DATA',
    'ARCHIVE',
    'DOCUMENTATION',
    'MISC'
]
for i in folders:
    os.makedirs(i)
