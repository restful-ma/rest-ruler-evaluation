import os

# directory in which all report files are located
work_dir = ''


# counts the appearances of each unique rule
rule_count = {}
# counts the appearances of each severity type
severity_type_count = {}
# counts the appearance of each software quality attribute
attributes_count = {}
# violation count per file
file_statistics = {}
# total violation count over all files
total_violations = 0
# all compiled violations
collection = []


def write_entry(filename, columns):
    entry = filename

    for i in range(1, len(columns) - 1 ):
        entry = entry + ';' + str(columns[i]).strip()
    collection.append(entry)


for file_name in os.listdir(work_dir):
    if file_name.endswith('.md'):
        print('opening file: ' + file_name)
        with open(work_dir + file_name, "r", encoding="utf8") as file:
            if file.readable():
                # ignore first 4 lines with title and column descriptions
                file.readline()
                file.readline()
                file.readline()
                file.readline()

                # first data entry
                line = file.readline()

                # counts individual violations per file
                file_violation_counter = 0

                while line:
                    # prepare data
                    columns = line.split("|")
                    # 10 entries first and last empty
                    # line --> 1,2 ; rule --> 3 ; category --> 4 ; severity --> 5 ;
                    # Rule type --> 6 ; attributes --> 7 ; improvement --> 8

                    # collection file
                    write_entry(file_name, columns)

                    # rule
                    rule = columns[3].strip()

                    if rule in rule_count.keys():
                        rule_count[rule] = rule_count[rule] + 1
                    else:
                        rule_count[rule] = 1

                    # severity
                    severity = columns[5].strip()

                    if severity in severity_type_count.keys():
                        severity_type_count[severity] = severity_type_count[severity] + 1
                    else:
                        severity_type_count[severity] = 1

                    # software quality attributes
                    attributes = columns[7].strip()

                    attribute_list = attributes.split(',')

                    for attribute in attribute_list:
                        attribute = attribute.strip()
                        if attribute in attributes_count.keys():
                            attributes_count[attribute] = attributes_count[attribute] + 1
                        else:
                            attributes_count[attribute] = 1

                    # increment counter for violations of file
                    file_violation_counter += 1

                    line = file.readline()

                # file statistics: violations per file
                total_violations += file_violation_counter
                file_statistics[file_name] = file_violation_counter


# output handling: creating a directory 'stats' with 5 output files

if not os.path.exists('stats'):
    os.mkdir('stats')

print('writing rules to file')
# write rule appearances
with open('stats/rule_output.csv', "w", encoding="utf8") as output_file:
    output_file.write('rule;appearances' + '\n')
    for rule, count in rule_count.items():
        output_file.write(rule + ';' + str(count) + '\n')

print('writing severities to file')
# write severity statistic
with open('stats/severity_output.csv', "w", encoding="utf8") as output_file:
    output_file.write('severity;appearances' + '\n')
    for severity, count in severity_type_count.items():
        output_file.write(severity + ';' + str(count) + '\n')

print('writing software quality attributes to file')
# write software attribute appearances
with open('stats/attributes_output.csv', "w", encoding="utf8") as output_file:
    output_file.write('attributes;appearances' + '\n')
    for attr, count in attributes_count.items():
        output_file.write(attr + ';' + str(count) + '\n')

print('writing violations to file')
# write number of violations per file
with open('stats/violation_output.csv', "w", encoding="utf8") as output_file:
    output_file.write('filename;violations' + '\n')
    for filename, count in file_statistics.items():
        output_file.write(filename + ';' + str(count) + '\n')

    output_file.write('total violations;' + str(total_violations))

with open('stats/violation_collection_output.csv', "w", encoding="utf8") as output_file:
    output_file.write('File name;Line No.;Line;Rule Violated;Category;Severity;Rule Type;Software Quality Attributes;Improvement Suggestion' + '\n')
    for entry in collection:
        output_file.write(entry + '\n')