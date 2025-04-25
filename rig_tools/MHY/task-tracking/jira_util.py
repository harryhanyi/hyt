import requests
from requests.auth import HTTPBasicAuth
import json


class JiraUtil:
    def __init__(self, base_url, user_email, api_token, project_key, pm):
        self.base_url = base_url
        self.project_key = project_key
        self.pm = pm
        self.auth = HTTPBasicAuth(
            user_email, 
            api_token
        )
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.assignees = self.query_assignees()
        self.tasks = self.query_tasks()
        if len(self.tasks) > 0:
            self.statuses = self.query_statuses()
        else:
            self.statuses = {}

    def query_assignees(self):
        # Set the endpoint URL
        endpoint = f"{self.base_url}/rest/api/3/user/assignable/search?project={self.project_key}"

        response = requests.request(
            "GET",
            endpoint,
            headers=self.headers,
            auth=self.auth
        )

        # Check the response status code
        if response.status_code != 200:
            print("Failed to query assignees. Error:", response.text)
            return False

        # Collect assignee name and account id
        assignees = {assignee['displayName']: assignee['accountId'] for assignee in response.json()}
        return assignees

    def query_statuses(self):
        # Set the endpoint URL
        keys = [key for key in self.tasks]
        endpoint = f"{self.base_url}/rest/api/3/issue/{keys[0]}/transitions"

        response = requests.request(
            "GET",
            endpoint,
            headers=self.headers,
            auth=self.auth
        )

        # Check the response status code
        if response.status_code != 200:
            print("Failed to query statuses. Error:", response.text)
            return False

        # Collect statuses
        statuses = {status["name"]: status["id"] for status in response.json()["transitions"]}
        return statuses

    def query_tasks(self):
        endpoint = f"{self.base_url}/rest/api/3/search"
        jql_query = f'project={self.project_key} AND issuetype = "Task"'
        fields = "summary, timetracking, status, duedate, assignee"
        params = {
            "jql": jql_query,
            "maxResults": 100,  # You can adjust the number of results per request
            "fields": fields,
        }
        response = requests.get(endpoint, params=params, auth=self.auth)

        # Check the response status code
        if response.status_code != 200:
            print("Failed to query tasks. Error:", response.text)
            return False

        tasks = {}
        for task in response.json()["issues"]:
            tasks[task["key"]] = {}
            tasks[task["key"]]["summary"] = task["fields"]["summary"]

            # Query estimate and timeSpent
            # Value is "" or int
            time_tracking = task["fields"].get("timetracking", {})
            tasks[task["key"]]["estimate"] = time_tracking.get("originalEstimateSeconds", "")
            if tasks[task["key"]]["estimate"] != "":
                tasks[task["key"]]["estimate"] = int(tasks[task["key"]]["estimate"] / 60 / 60) # Unit is hour
            tasks[task["key"]]["remaining"] = time_tracking.get("remainingEstimateSeconds", "")
            if tasks[task["key"]]["remaining"] != "":
                tasks[task["key"]]["remaining"] = int(tasks[task["key"]]["remaining"] / 60 / 60) # Unit is hour
            tasks[task["key"]]["timeSpent"] = ""
            if tasks[task["key"]]["estimate"] != "" and tasks[task["key"]]["estimate"] != "":
                tasks[task["key"]]["timeSpent"] = tasks[task["key"]]["estimate"] - tasks[task["key"]]["remaining"]

            tasks[task["key"]]["status"] = task["fields"]["status"]["name"]
            tasks[task["key"]]["dueDate"] = task["fields"]["duedate"]

            tasks[task["key"]]["assignee"] = ""
            if task["fields"]["assignee"] and task["fields"]["assignee"]["displayName"]:
                tasks[task["key"]]["assignee"] = task["fields"]["assignee"]["displayName"]
        return tasks

    def filter_task_by_assignee(self, assignee):
        task_by_assignee = {}
        for task_key in self.tasks:
            if self.tasks[task_key]["assignee"] == assignee:
                task_by_assignee[task_key] = self.tasks[task_key]
        return task_by_assignee

    def create_task(self, summary, due_date, estimate, assignee, issue_type="Task"):
        # Set the endpoint URL
        endpoint = f"{self.base_url}/rest/api/3/issue/"

        # Set the request payload
        payload = {
            "fields": {
                "project": {
                    "key": self.project_key
                },
                "summary": summary,
                "duedate": due_date,
                "timetracking": {
                    "originalEstimate": f"{estimate}h"
                },
                "assignee": {
                    "id": self.assignees[assignee]
                },
                # "reporter": {
                #     "id": self.assignees[self.pm]
                # },
                "issuetype": {
                    "name": issue_type  # Set the task type accordingly
                }
            }
        }

        # Send the POST request to create the task
        response = requests.request(
            "POST", 
            endpoint, 
            data=json.dumps(payload),
            headers=self.headers, 
            auth=self.auth, 
        )

        # Check the response status code
        if response.status_code != 201:
            print("Failed to create task. Error:", response.text)
            return False
        return True

    def delete_task(self, key):
        # Set the endpoint URL
        endpoint = f"{self.base_url}/rest/api/3/issue/{key}"

        response = requests.request(
            "DELETE",
            endpoint,
            auth=self.auth
        )

        # Check the response status code
        if response.status_code != 204:
            print("Failed to delete task. Error:", response.text)
            return False
        return True
    
    def edit_task(self, task_key, key, value):
        # Set the endpoint URL
        endpoint = f"{self.base_url}/rest/api/3/issue/{task_key}"
        if key == "status": # Status
            endpoint = endpoint + "/transitions"
        elif key == "log": # Work Log
            endpoint = endpoint + "/worklog"

        # Set the request payload 
        payload = {}
        if key == "estimate": # Estimate
            payload = {
                "fields": {
                    "timetracking": {
                        "originalEstimate": value + "h" # hour unit
                    }
                }
            }
        elif key == "assignee": # Assignee
            payload = {
                "fields": {
                    "assignee": {
                        "accountId": self.assignees[value]
                    }
                }
            }
        elif key == "status": # Status
            payload = {
                "transition": {
                    "id": self.statuses[value]
                }
            }
        elif key == "log": # Work Log
            payload = {
                "timeSpentSeconds": int(value) * 60 * 60
            }
        else:
            payload = {
                "fields": {
                    key: value
                }
            }

        # Send the PUT request to edit the task
        request_type = "PUT"
        if key == "status" or key == "log":
            request_type = "POST"
        
        response = requests.request(
            request_type,
            endpoint, 
            data=json.dumps(payload), 
            headers=self.headers, 
            auth=self.auth
        )

        # Check the response status code
        check_code = 204
        if key == "log":
            check_code = 201

        if response.status_code != check_code:
            print("Failed to edit task. Error:", response.text)
            return False
        return True
    
