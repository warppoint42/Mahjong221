import csv

stats = dict()

with open('unifiedroundlog.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile, ('AI', 'gameID', 'end', 'win', 'feed', 'riichi'))
    for row in reader:
        if row['AI'] not in stats:
            stats[row['AI']] = dict()
        stats[row['AI']].setdefault('n', 0)
        stats[row['AI']].setdefault('end', 0)
        stats[row['AI']].setdefault('win', 0)
        stats[row['AI']].setdefault('feed', 0)
        stats[row['AI']]['n'] += 1
        if row['end'] == '1':
            stats[row['AI']]['end'] += 1
        if row['win'] == '1':
            stats[row['AI']]['win'] += 1
        if row['feed'] == '1':
            stats[row['AI']]['feed'] += 1

with open('owari.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile, ('AI', 'gameID', '1', '2', '3', '4'))

    for row in reader:
        stats[row['AI']].setdefault('1', 0)
        stats[row['AI']].setdefault('2', 0)
        stats[row['AI']].setdefault('3', 0)
        stats[row['AI']].setdefault('4', 0)
        stats[row['AI']].setdefault('totp', 0)
        stats[row['AI']].setdefault('totn', 0)
        stats[row['AI']]['totn'] += 1
        if 'Name' in row['1']:
            stats[row['AI']]['1'] += 1
            stats[row['AI']]['totp'] += 1
        if 'Name' in row['2']:
            stats[row['AI']]['2'] += 1
            stats[row['AI']]['totp'] += 2
        if 'Name' in row['3']:
            stats[row['AI']]['3'] += 1
            stats[row['AI']]['totp'] += 3
        if 'Name' in row['4']:
            stats[row['AI']]['4'] += 1
            stats[row['AI']]['totp'] += 4

print(stats)



