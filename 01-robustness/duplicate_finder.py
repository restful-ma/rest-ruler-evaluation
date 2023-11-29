
collection = {}
duplicate = []

with open("apis.csv", "r", encoding="utf8") as f:
    if f.readable():
        # ignore first line with column descriptions
        f.readline()
        line = f.readline()
        while line:
            # prepare datano
            columns = line.split(";")
            title = columns[0]
            categories = columns[1]
            version = columns[2]
            url = columns[3]

            if title == '':
                title = 'empty'

            if title in collection.keys():
                newList = collection.get(title)
                newList.append(line)
                collection[title] = newList
                if title not in duplicate:
                    duplicate.append(title)
            else:
                collection[title] = [line]
            print([title])

            line = f.readline()

with open("duplicate_out.csv", "w", encoding="utf8") as out:
    out.write("title;x-apisguru-categories;openapiVer;swaggerUrl\n")

    for title in duplicate:
        for entry in collection.get(title):
            out.write(entry)