import exercise


path = "../../tests/provisory_cases_v4/"
file_begin = "T"
output_end = "_output"
input_end = "_input"
file_end = ".txt"
failed_tests = []
tests = range(21)

for i in tests:
    f = open(path + file_begin + "{:02d}".format(i) + input_end + file_end, "r")

    print("For file " + str(i) + ":")
    try:
        output = exercise.test_lines(f.readlines())
    except Exception as e:
        print("Exception ocurred -> " + str(e.args) + "\n")
        failed_tests.append(i)
        continue

    expected_output = open(path + file_begin + "{:02d}".format(i) + output_end + file_end, "r").read()
    test_result = "PASSED"
    print("For file " + str(i) + ":")
    for line, (g_line, e_line) in enumerate(zip(output.split('\n'), expected_output.split('\n'))):

        line_result = e_line == g_line
        if line_result and e_line == "":
            break
        if not line_result:
            test_result = "FAILED"

        print('\tL' + str(line) + "-Expected:  " + e_line + "\n\tL" + str(line) + "-Got:       " + g_line + "\n\t\tResult: " + str(line_result))

    print("TEST " + test_result + '\n')
    if test_result == "FAILED":
        failed_tests.append(i)
print("RESULT: (" + str(len(tests) - len(failed_tests)) + "/" + str(len(tests)) + ")\tFAILED: " + str(failed_tests))