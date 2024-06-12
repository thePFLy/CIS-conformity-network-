from collections import deque
from inquirer import prompt, Checkbox
from re import split



class Selection:
    def __init__(self, data: dict, label: str, device_selection: bool, auto_sort: bool = False) -> None:
        self.results = {
            "resultats": []
        }
        self.label = label
        self.is_device = device_selection
        self.temp = data
        self.device_selection(data=data) if self.is_device else self.recursive_traversal()
        if auto_sort:
            self.results["resultats"] = sorted(self.results['resultats'], key=self.numeric_sort_key)
    
    def construct_options(self, data: dict):
        result = []
        if not self.is_device:
            for item in data:
                if item != "description" and "description" in data[item]:
                    result.append(f'[{item}] {data[item]["description"]}')
        else:
            for item in data:
                result.append(f'[{item}] {data[item]["ip"]}')
        return result
    
    def make_selection(self, data: dict):
        return Checkbox(
            self.label,
            message="Choix",
            choices=self.construct_options(data=data)
        )
    def points(self, result: list):
        tab = []
        for choice in result[self.label]:
            tab.append(str(choice).split("]")[0][1:].strip())
        return tab
    
    def question(self, data: dict):
        result = prompt([self.make_selection(data)])
        selected_indices = self.points(result=result)
        self.result_add(result_selection=selected_indices)
        return selected_indices
    
    def result_add(self, result_selection: list):
        for element in result_selection:
            self.results['resultats'].append(element)

    def device_selection(self, data: dict):
        self.question(data=data)

    def recursive_traversal(self):
        queue = deque([(self.label, self.temp)])  # Utilisation d'une file d'attente (FIFO) avec une étiquette

        while queue:
            label, data = queue.popleft()  # Unpack the tuple to get the label and the dictionary

            # Si le dictionnaire contient des options sélectionnables
            if any("description" in data[item] and not "set_command" in data[item] for item in data if item != "description"):
                selected_indices = self.question(data)
            else:
                selected_indices = []

            for index in selected_indices:
                if index in data and isinstance(data[index], dict):
                    queue.append((index, data[index]))

    
    def numeric_sort_key(self, value):
        parts = split(r'\.', value)
        return [int(part) for part in parts]