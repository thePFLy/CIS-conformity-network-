class Score:
    def __init__(self, result_list: list) -> None:
        self.score = 0
        self.score_max = len(result_list)
        self.results = {}

    def increment(self):
        self.score += 1

    def result(self, n_test: str, is_success: bool, description: str, get_result: str):
        self.results[n_test] = {}
        self.results[n_test]["result"] = is_success
        self.results[n_test]["description"] = description
        self.results[n_test]["get_result"] = get_result
        if is_success:
            self.increment()

    def __str__(self) -> str:
        return f"{self.score}/{self.score_max}"