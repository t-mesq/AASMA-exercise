import exercise


path = "../../tests/provisory_cases_v4/"
file_begin = "T"
output_end = "_output"
input_end = "_input"
file_end = ".txt"

for i in range(12):
    f = open(path + file_begin + "{:02d}".format(i) + input_end + file_end, "r")

    try:
        output = exercise.test_lines(f.readlines())
    except Exception as e:
        output = "Exception ocurred -> " + str(e.args) + "\n"

    expected_output = open(path + file_begin + "{:02d}".format(i) + output_end + file_end, "r").read()

    result = output == expected_output

    print("For file " + str(i) + ":\n" + "Expected:   " + expected_output + "Got:        " + output + "Result: " + str(result) + "\n")

