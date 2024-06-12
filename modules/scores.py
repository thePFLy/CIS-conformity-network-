class Score:
    def __init__(self, result_list: list) -> None:
        self.score = 0
        self.score_max = len(result_list)
        self.results = {}

    def increment(self):
        self.score += 1

    def result(self, n_test: str, is_success: bool):
        self.results[n_test] = is_success
        if is_success:
            self.increment()