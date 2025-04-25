import json

class JSONReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._read_json()

    def _read_json(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def get_solvers(self):
        return self.data.get('solvers', [])

    def get_solver_by_name(self, solver_name):
        for solver in self.get_solvers():
            if solver['name'] == solver_name:
                return solver
        return None

