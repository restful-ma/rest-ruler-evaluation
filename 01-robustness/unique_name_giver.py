
names = {}

# customize input and output file names
input_filename = ''
output_filename = 'unique_duplicates.csv'


# recursive function to calculate the required amount of reserved chars needed
def check_increment_size(number):
    if number > 10:
        return 1 + check_increment_size(number / 10)
    else:
        return 1


def check_characters_need(file_title):
    increment = names.get(file_title, 1)

    return check_increment_size(increment)


# supportive method to provide unique naming of titles
def create_unique_name(columns):
    string = ''

    if len(columns) == 0:
        return string

    name = columns[0]
    # change name to a new unique name
    # as report generation cuts titles off at 30 chars unique naming needs to be added in these 30 chars
    digits = check_characters_need(name)
    if len(name) > (32 - digits) and digits < 32:
        columns[0] = name[0: (30 - digits)] + str(names.get(name))
    else:
        columns[0] = name + str(names.get(name))
    # increment identifier
    names[title] = names.get(name) + 1

    # reconstruct initial line
    for i in range(0, len(columns) - 1):
        string = string + columns[i] + ';'
    string = string + columns[-1]
    return string


with open(input_filename, "r", encoding="utf8") as file:
    with open(output_filename, "w", encoding="utf8") as outputFile:
        if file.readable():
            # copy first line with column descriptions to output file
            outputFile.write(file.readline())
            line = file.readline()
            while line:
                # prepare data
                columns = line.split(";")
                title = str(columns[0])

                if title in names:
                    print('title: ' + title + ' has a duplicate. Applying name change')
                    outputFile.write(create_unique_name(columns))
                else:
                    # first occurrence of name
                    names[title] = 1
                    outputFile.write(line)
                line = file.readline()
