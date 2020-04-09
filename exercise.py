import sys
import math


def standard_output(text):
    sys.stdout.write(text)


def test_output(text):
    global test_channel
    test_channel += text


def weighted_average(weights_n_values, discount_factor):
    weighted_values = 0
    weighted_sum = sum(map(lambda x: x ** discount_factor, weights_n_values.keys()))
    for weight, value in weights_n_values.items():
        weighted_values += (value * (weight ** discount_factor)) / weighted_sum
    return weighted_values


def get_coefficients(negative_utility, positive_utility):
    negative_coefficient = positive_utility / (positive_utility - negative_utility)
    return negative_coefficient, 1 - negative_coefficient


def filter_Nvalues(dict):
    return {k: v for k, v in dict.items() if v < 0}


def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier + 0.5) / multiplier


def dict_to_string(dictionary, float_precision=2, openS="{", assignment="=", separator=",", closeS="}",
                   inner_dict_transform=None):
    if inner_dict_transform is None:
        inner_dict_transform = lambda x: dict_to_string(x, float_precision, openS, assignment, separator, closeS)
    dict_string = ""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            parsed_value = openS + inner_dict_transform(value) + closeS
        elif isinstance(value, float):
            parsed_value = str("{:." + str(float_precision) + "f}").format(value)
        else:
            parsed_value = str(value)
        dict_string += str(key) + assignment + parsed_value + separator
    return dict_string[:-1]


def string_to_dict(string_dict, openS="{", assignment="=", separator=",", closeS="}", inner_dict_transform=None):
    def get_enclosed(string):
        begin, end = string.split(openS, 1)
        rest = end
        middle = ""
        depth = 1
        Cindex = 0
        while depth > 0:
            Oindex = rest.find(openS)
            Cindex = rest.find(closeS)
            if Cindex == -1:
                return
            if Oindex == -1 or Oindex > Cindex:
                depth -= 1
                middle = rest[:Cindex + 1:]
                rest = rest[Cindex + 1:]
            else:
                depth += 1
                middle = rest[:Cindex + 1:]
                rest = rest[Oindex + 1:]
        return begin, middle, rest

    if inner_dict_transform is None:
        inner_dict_transform = lambda x: string_to_dict(x, openS, assignment, separator, closeS)
    dict_string = {}
    leftover = string_dict
    while assignment in leftover:
        key, leftover = leftover.split(assignment, 1)
        if leftover[0] == openS:
            _, value, leftover = get_enclosed(leftover)
            value = inner_dict_transform(value)
            if separator in leftover:
                _, leftover = leftover.split(separator, 1)
        else:
            if separator in leftover:
                value, leftover = leftover.split(separator, 1)
            else:
                value, leftover = leftover, ""
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    value = str(value)
        dict_string[key] = value
    return dict_string


#########################
### A: AGENT BEHAVIOR ###
#########################

class Society:
    def __init__(self, options):
        self.agents = {"A": None}
        self.agent_options = {"restart": 0, "cycle": 1, "memory-factor": 0.0, "decision": "rationale", "verbose": False}
        self.decisions = {
            "mono-society": {
                "perceive": self.__mono_perceive,
                "recharge": self.__mono_recharge
            },
            "homogeneous-society": {
                "perceive": self.__homogeneous_perceive,
                "recharge": self.__geneous_recharge
            },
            "heterogeneous-society": {
                "perceive": self.__heterogeneous_perceive,
                "recharge": self.__geneous_recharge
            }
        }
        self.options = {"decision": self.decisions["mono-society"]}
        self.perceived = []
        agent_decisions = ("rationale", "flexible")
        for assignment in options:
            option, value = assignment.split("=", 1)
            if option == "agents":
                agent_list = value.replace("{", "").replace("{", "").replace("[", "").replace("]", "").split(",")
                self.agents = dict.fromkeys(agent_list, None)
            elif option in self.options:
                if option == "decision":
                    if value in self.decisions:
                        self.options[option] = self.decisions[value]
                    elif value in agent_decisions:
                        self.agent_options[option] = value
            else:
                self.agent_options[option] = eval(value, {})
        for agent in self.agents:
            self.agents[agent] = Agent(dict_to_string(self.agent_options, separator=" ").split(' '))

    def __mono_perceive(self, task_ID, assignment):
        self.agents[task_ID].perceive("A " + assignment)

    def __homogeneous_perceive(self, _, assignment):
        task, utility = assignment.split("=", 1)
        self.perceived.append(float(utility))
        if len(self.perceived) == len(self.agents):
            average = sum(self.perceived) / len(self.perceived)
            for _, agent in self.agents.items():
                agent.perceive("A u=" + str(average))

    def __heterogeneous_perceive(self, task_ID, assignment):
        self.agents[task_ID].perceive("A " + assignment)

    def __mono_recharge(self):
        return list(self.agents.values())[0].recharge()

    def __geneous_recharge(self):
        agents_recharge = {"state": {}, "gain": 0}
        for agent_ID, agent in self.agents.items():
            agent_recharge = agent.recharge()
            agents_recharge["state"][agent_ID] = agent_recharge["state"]
            agents_recharge["gain"] += agent_recharge["gain"]
        return agents_recharge

    def perceive(self, input):
        task_ID, assignment = input.split()

        if task_ID in self.agents:
            self.options["decision"]["perceive"](task_ID, assignment)
        else:
            for _, agent in self.agents.items():
                agent.perceive(input)

    def decide_act(self):
        self.perceived = []
        for _, agent in self.agents.items():
            agent.decide_act()

    def recharge(self):
        return self.options["decision"]["recharge"]()


class Agent:
    def __init__(self, options):
        self.tasks = {"u": {}}
        self.tasks_in_execution = None
        self.expected_wait = 0
        self.executed_tasks = set()
        self.gain = 0
        self.tick = 0
        self.options = {"restart": 0, "cycle": 1, "memory-factor": 0.0, "verbose": False}
        traits = {"rationale": "rationale", "flexible": "flexible"}

        for assignment in options:
            option, value = assignment.split("=", 1)
            self.options[option] = eval(value, traits)

    def __try_flexible_decision(self, weighted_average_utilities, most_utility_task):
        if self.options["decision"] == "flexible":
            weighted_average_pos_utilities = {k: weighted_average_utilities[k] for k, v in
                                              self.tasks["u"].items() if min(v.values()) >= 0}
            if len(weighted_average_pos_utilities) != 0:
                # if there are positive utility tasks, try flexible decision
                most_utility_pos_task = max(weighted_average_pos_utilities,
                                            key=weighted_average_pos_utilities.get)  # get task with most utility
                if most_utility_pos_task != most_utility_task:
                    # if best task can generate negative utility, try flexible decision
                    weighted_average_neg_utilities = {k: weighted_average(filter_Nvalues(v), self.options["memory-factor"])
                                                      for k, v in self.tasks["u"].items()
                                                      if k not in weighted_average_pos_utilities}
                    expected_gain = positive_utility = weighted_average_pos_utilities[most_utility_pos_task]
                    most_flexible_task = most_utility_pos_task
                    most_flexible_cofs = (1, 0)
                    for negative_task, negative_utility in weighted_average_neg_utilities.items():
                        if weighted_average_utilities[negative_task] < expected_gain:
                            continue
                        negative_cof, positive_cof = get_coefficients(negative_utility, positive_utility)
                        possible_gain = negative_cof * weighted_average_utilities[negative_task] + positive_cof * positive_utility
                        if possible_gain > expected_gain:
                            expected_gain = possible_gain
                            most_flexible_task = negative_task
                            most_flexible_cofs = (negative_cof, positive_cof)

                    if self.options["verbose"]:
                        print("\tagent switched task " + str(
                            list(self.tasks_in_execution)[0]) + " with task " + most_utility_task)
                    self.tasks_in_execution = {most_flexible_task: most_flexible_cofs[0],
                                               most_utility_pos_task: most_flexible_cofs[1]}
                    if most_flexible_task < most_utility_pos_task:
                        output_to("{" + most_flexible_task + "=" + "{:.2f}".format(round_half_up(most_flexible_cofs[0], 2)) + "," +
                                  most_utility_pos_task + "=" + "{:.2f}".format(1 - round_half_up(most_flexible_cofs[0], 2)) + '}\n')
                    else:
                        output_to("{" + most_utility_pos_task + "=" + "{:.2f}".format(1 - round_half_up(most_flexible_cofs[0], 2)) + "," +
                                  most_flexible_task + "=" + "{:.2f}".format(round_half_up(most_flexible_cofs[0], 2)) + '}\n')
                    self.expected_wait = max(self.options["restart"] - 1, 0)
                    return True
        return False

    def perceive(self, input):
        task_ID, assignment = input.split()
        info, value = assignment.split("=", 1)

        if task_ID == "A":
            if value[0] != "{":
                task_ID = list(self.tasks_in_execution)[0]
                self.gain += float(value)
                if list(self.tasks_in_execution)[0] not in self.executed_tasks:
                    self.executed_tasks.add(task_ID)
                    self.tasks[info][list(self.tasks_in_execution)[0]] = {}
                self.tasks[info][list(self.tasks_in_execution)[0]][self.tick] = float(value)
                if self.options["verbose"]:
                    print("\tagent assigned task " + list(self.tasks_in_execution)[0] + " with utility " + value)

            else:
                assignments = value.replace("{", "").replace("}", "").split(",")
                for assignment in assignments:
                    task_ID, value = assignment.split("=", 1)
                    self.gain += float(value) * self.tasks_in_execution[task_ID]
                    if task_ID not in self.executed_tasks:
                        self.executed_tasks.add(task_ID)
                        self.tasks[info][task_ID] = {}
                    self.tasks[info][task_ID][self.tick] = float(value)
                    if self.options["verbose"]:
                        print("\tagent assigned task " + task_ID + " with utility " + value)

        else:
            self.tasks[info][task_ID] = {1: float(value)}
            if self.options["verbose"]:
                print("\tagent assigned task " + task_ID + " with utility " + value)

    def decide_act(self):
        self.tick += 1
        if self.options["cycle"] - self.tick < self.options["restart"]:  # no point in changing
            return

        weighted_average_utilities = {k: weighted_average(v, self.options["memory-factor"]) for k, v in
                                      self.tasks["u"].items()}
        most_utility_task = max(weighted_average_utilities,
                                key=weighted_average_utilities.get)  # get task with most utility

        if not self.__try_flexible_decision(weighted_average_utilities, most_utility_task):

            should_switch = self.tasks_in_execution is None
            could_switch = should_switch or most_utility_task != list(self.tasks_in_execution)[0]

            if could_switch and not should_switch:
                expected_gain = weighted_average_utilities[list(self.tasks_in_execution)[0]] * (self.options["cycle"] - self.tick - self.expected_wait + 1)
                possible_gain = weighted_average_utilities[most_utility_task] * (self.options["cycle"] - self.tick - self.options["restart"] + 1)
                should_switch = (expected_gain < possible_gain) or ((expected_gain == possible_gain) and (most_utility_task < list(self.tasks_in_execution)[0]))

            if should_switch:
                if self.options["verbose"]:
                    print("\tagent switched task " + str(list(self.tasks_in_execution)[0]) + " with task " + most_utility_task)
                self.tasks_in_execution = {most_utility_task: 1.0}
                self.expected_wait = max(self.options["restart"] - 1, 0)

            else:
                if self.options["verbose"]:
                    print("\tagent maintained task " + list(self.tasks_in_execution)[0])
                self.expected_wait = max(self.expected_wait - 1, 0)  # update wait

    def recharge(self):
        return {"state": {k: weighted_average(v, self.options["memory-factor"]) if k in self.executed_tasks else "NA" for k, v in self.tasks["u"].items()}, "gain": self.gain}


#####################
### B: MAIN UTILS ###
#####################

output_to = standard_output
test_channel = ""


def main():
    global output_to
    output_to = standard_output

    # print(string_to_dict("cycle=5 agents={A1=2,A2=fsf} decision=society restart=0", separator=" ",inner_dict_transform=string_to_dict))
    line = sys.stdin.readline()
    society = Society(line.split(' '))
    for line in sys.stdin:
        if line.startswith("end"):
            break
        elif line.startswith("TIK"):
            society.decide_act()
        else:
            society.perceive(line)
    sys.stdout.write(dict_to_string(society.recharge(), separator=" ", inner_dict_transform=dict_to_string) + '\n')


def test_lines(lines):
    global output_to
    global test_channel

    test_channel = ""
    output_to = test_output

    line = lines[0]
    society = Society(line.split(' '))
    for line in lines[1:]:
        if line.startswith("end"):
            break
        elif line.startswith("TIK"):
            society.decide_act()
        else:
            society.perceive(line)
    return test_channel + dict_to_string(society.recharge(), separator=" ", inner_dict_transform=dict_to_string) + '\n'


if __name__ == "__main__":
    main()
