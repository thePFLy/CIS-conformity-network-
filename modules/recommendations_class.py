from json import load


class Recommendation:
    def __init__(self, filename: str = "ressources/recommendations.json") -> None:
        self.filename = f"ressources/{filename}.json"

    def read_file(self):
        with open(self.filename, "r") as file:
            return load(file)
        
    def compare(self, generated_response: str, waited_response: str):
        print(generated_response, waited_response)