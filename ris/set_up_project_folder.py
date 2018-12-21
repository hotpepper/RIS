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
    '*.zip',
    r'DATA/**',
    r'ARCHIVE/**',
    r'MISC/**'
]
for i in exts:
    f.write(i+'\n')
f.close()

folders = [
    'DATA',
    'ARCHIVE',
    'DOCUMENTATION',
    'MISC'
]
for i in folders:
    os.makedirs(i)
