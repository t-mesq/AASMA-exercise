import sys

def weighted_average(weights_n_values, discount_factor):
    weighted_values = 0
    weighted_sum = sum(map(lambda x: x ** discount_factor, weights_n_values.keys()))
    for weight, value in weights_n_values.items():
        weighted_values += (value * (weight ** discount_factor)) / weighted_sum
    return weighted_values


#########################
### A: AGENT BEHAVIOR ###
#########################

class Agent:
    def __init__(self, options):
        self.tasks = {"u": {}}
        self.task_in_execution = None
        self.expected_wait = 0
        self.executed_tasks = set()
        self.gain = 0
        self.tick = 0
        self.options = {"restart": 0, "cycle": 1, "memory-factor": 0.3, "verbose": False}
        traits = {"rationale": "rationale", "flexible": "flexible"}

        for assignment in options:
            option, value = assignment.split("=", 1)
            self.options[option] = eval(value, traits)

    def perceive(self, input):
        task_ID, assignment = input.split()
        info, value = assignment.split("=", 1)

        if task_ID == "A":
            task_ID = self.task_in_execution
            self.gain += float(value)
            if self.task_in_execution not in self.executed_tasks:
                self.executed_tasks.add(task_ID)
                self.tasks[info][self.task_in_execution] = {}
            self.tasks[info][self.task_in_execution][self.tick] = float(value)
            if self.options["verbose"]:
                print("\tagent assigned task " + self.task_in_execution +" with utility " + value)

        else:
            self.tasks[info][task_ID] = {1: float(value)}
            if self.options["verbose"]:
                print("\tagent assigned task " + task_ID +" with utility " + value)

    def decide_act(self):
        self.tick += 1
        if self.options["cycle"] - self.tick < self.options["restart"]:  # no point in changing
            return

        weighted_average_utilities = {k: weighted_average(v, self.options["memory-factor"]) for k, v in
                                      self.tasks["u"].items()}
        most_utility_task = max(weighted_average_utilities,
                                key=weighted_average_utilities.get)  # get task with most utility

        could_switch = most_utility_task != self.task_in_execution
        should_switch = self.task_in_execution is None

        if could_switch and not should_switch:
            expected_gain = weighted_average_utilities[self.task_in_execution] * (
                    self.options["cycle"] - self.tick - self.expected_wait + 1)
            possible_gain = weighted_average_utilities[most_utility_task] * (
                    self.options["cycle"] - self.tick - self.options["restart"] + 1)
            should_switch = (expected_gain < possible_gain) or (
                    (expected_gain == possible_gain) and (most_utility_task < self.task_in_execution))

        if should_switch:
            if self.options["verbose"]:
                print("\tagent switched task " + str(self.task_in_execution) +" with task " + most_utility_task)
            self.task_in_execution = most_utility_task
            self.expected_wait = max(self.options["restart"] - 1, 0)

        else:
            if self.options["verbose"]:
                print("\tagent maintained task " + self.task_in_execution)
            self.expected_wait = max(self.expected_wait - 1, 0)  # update wait

    def recharge(self):
        output = "state={"
        for key, val in self.tasks["u"].items():
            achieved_val = "{:.2f}".format(
                weighted_average(val, self.options["memory-factor"])) if key in self.executed_tasks else "NA"
            output += key + "=" + achieved_val + ","
        return output[:-1] + "} gain=" + "{:.2f}".format(self.gain)


#####################
### B: MAIN UTILS ###
#####################

def main():
    line = sys.stdin.readline()
    agent = Agent(line.split(' '))
    for line in sys.stdin:
        if line.startswith("end"):
            break
        elif line.startswith("TIK"):
            agent.decide_act()
        else:
            agent.perceive(line)
    sys.stdout.write(agent.recharge() + '\n')


def test_lines(lines):
    line = lines[0]
    agent = Agent(line.split(' '))
    for line in lines[1:]:
        if line.startswith("end"):
            break
        elif line.startswith("TIK"):
            agent.decide_act()
        else:
            agent.perceive(line)
    return agent.recharge() + '\n'


if __name__ == "__main__":
    main()
