LangSmith mock
----

LangSmith mock server.

# Getting Started

Start LangSmith mock server.

```sh
export LANGSMITH_MOCK_REPO_OWNER=me
python langsmith_mock/langsmith_mock.py
```

Push prompt template to LangSmith mock server.

```python
from langchain.prompts.prompt import PromptTemplate
from langchain import hub
import os
os.environ["LANGCHAIN_HUB_API_URL"] = "http://localhost:3000/"

prompt = PromptTemplate.from_template("hello {name}")
resp = hub.push(
    repo_full_name="me/hello",
    object=prompt,
    api_url="http://localhost:3000/"
)
print(resp)
```

Pull prompt template from LangSmith mock server.

```python
from langchain import hub
import os
os.environ["LANGCHAIN_HUB_API_URL"] = "http://localhost:3000/"

prompt = hub.pull(
    "me/hello:latest",
    api_url="http://localhost:3000/"
)
print(prompt.invoke({"name": "mock"}))
```

Post run log to LangSmith mock server,
and mock server write log file under ``data/runs``.

```python
from langchain import hub
from uuid import uuid4
import os

unique_id = uuid4().hex[0:8]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = f"trace - {unique_id}"
os.environ["LANGCHAIN_ENDPOINT"] = "http://localhost:3000/"
os.environ["LANGCHAIN_API_KEY"] = "dummy"
os.environ["LANGCHAIN_HUB_API_URL"] = "http://localhost:3000/"

prompt = hub.pull(
    "me/hello:latest",
)
print(prompt.invoke({"name": "mock"}))
```
