from faker import Faker
from locust import HttpUser, task, TaskSet, constant_throughput
import random
import re

fake = Faker('ru_RU')

SUBJECTS = ['russian', 'informatics', 'geographic', 'biology', 'history', 'literature']
TEST_IDS = [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14]
ANSWER_RE = re.compile(r'name="(question_\d+)" id="choice_\d+" value="(\d+)"')


class StudentTests(TaskSet):
    def csrf(self):
        return self.client.cookies.get('csrftoken')

    def on_start(self):
        username = fake.user_name() + str(random.randint(1000, 99999))
        password = fake.password(length=12)

        self.client.get('/signup')
        self.client.post('/signup', data={
            'csrfmiddlewaretoken': self.csrf(),
            'username': username,
            'password1': password,
            'password2': password,
        })
        self.client.post('/login', data={
            'csrfmiddlewaretoken': self.csrf(),
            'username': username,
            'password': password,
        })
        self.open_test()

    @task(5)
    def open_home(self):
        self.client.get('/')

    @task(5)
    def open_subject(self):
        self.client.get('/' + random.choice(SUBJECTS), name='/[предмет]')

    @task(5)
    def open_test_list(self):
        self.client.get('/tests/test_list')

    @task(5)
    def open_test(self):
        self.test_url = f'/tests/{random.choice(TEST_IDS)}'
        page = self.client.get(self.test_url, name='/tests/[id]')

        self.answers = {}
        for question, choice in ANSWER_RE.findall(page.text):
            self.answers.setdefault(question, []).append(choice)

    @task(5)
    def open_results(self):
        self.client.get('/tests/test_result/')

    @task(5)
    def open_contact_form(self):
        self.client.get('/contact_form/')

    @task(1)
    def pass_test(self):
        data = {question: random.choice(choices) for question, choices in self.answers.items()}
        data['csrfmiddlewaretoken'] = self.csrf()
        self.client.post(self.test_url, data=data, name='/tests/[id]')

    @task(1)
    def register_user(self):
        password = fake.password(length=12)
        self.client.post('/signup', data={
            'csrfmiddlewaretoken': self.csrf(),
            'username': fake.user_name() + str(random.randint(1000, 99999)),
            'password1': password,
            'password2': password,
        })


class WebsiteUser(HttpUser):
    wait_time = constant_throughput(1)
    tasks = [
        StudentTests
    ]
