class Score:
    def __init__(self, result_list: list) -> None:
        self.score = 0
        self.score_max = len(result_list)
        self.results = {}

    def increment(self):
        self.score += 1

    def result(self, n_test: str, is_success: bool, description: str, get_result: str, expected: str, command: str, ip: str, level: str):
        self.results["title"] = ip
        self.results[n_test] = {}
        self.results[n_test]["result"] = is_success
        self.results[n_test]["description"] = description
        self.results[n_test]["get_result"] = get_result
        self.results[n_test]["expected"] = expected
        self.results[n_test]["command"] = command
        self.results[n_test]["level"] = level
        if is_success:
            self.increment()

    def save(self):
        text = ""
        max = len(self.results) - 1
        fail = 0
        for test in self.results:
            if test == "title":
                header = f"+ --- || {self.results['title']} || --- +\n"
            elif not self.results[test]["result"]:
                text += f"+ ----- Test n° {test} ---------------------------------\n"
                text += f"| - Description: {self.results[test]['description']}\n"
                text += f"| - Level CIS: {self.results[test]['level']}\n"
                fail += 1
        header += f"| - {max - fail} test{'s' if (max - fail) == 1 else None} sur {max} passés...\n"
        header += f"|  > Tests réussis: {max - fail}\n"
        header += f"|  > Tests échoués: {fail}\n"
        header += "+ --- Détails des tests échoués: ---------------------------- +\n"

        text = header + text
        with open(file=f"rapport/{self.results['title']}.txt", mode="w", encoding="utf-8") as file:
            file.write(text)
        print(f"Un rapport à été généré dans /rapport/{self.results['title']}.txt")