from json import load


class Recommendation:
    def __init__(self, filename: str = "ressources/recommendations.json") -> None:
        self.filename = filename

    def read_file(self):
        with open(self.filename, "r") as file:
            return load(file)