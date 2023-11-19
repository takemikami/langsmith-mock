import os
import json
import hashlib
import glob
import pathlib
import fcntl
import time

from flask import Flask, request, abort

app = Flask(__name__)

repo_owner = os.environ.get("LANGSMITH_MOCK_REPO_OWNER", "owner")
data_dir = os.environ.get("LANGSMITH_MOCK_DATADIR", "data")
if not os.path.isabs(data_dir):
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", data_dir))


# Hub - get repo
@app.route("/repos/<owner>/<repo>", methods=['GET'])
def repo_get(owner, repo):
    repo_dir = os.path.join(data_dir, "hub", owner, repo)
    if not os.path.isdir(repo_dir):
        abort(404)
    return {}


# Hub - create repo
@app.route("/repos/", methods=['POST'])
def repo_create():
    repo = request.json["repo_handle"]
    repo_dir = os.path.join(data_dir, "hub", repo_owner, repo)
    os.makedirs(repo_dir, exist_ok=True)
    return {}


# Hub - get commits list
@app.route("/commits/<owner>/<repo>/", methods=['GET'])
def commits_list(owner, repo):
    repo_dir =os.path.join(data_dir, "hub", owner, repo)
    commits = sorted(
        [
            {
                "commit_hash": os.path.basename(e),
                "mtime": pathlib.Path(e).stat().st_mtime
            } for e in glob.glob(os.path.join(repo_dir, "*"))
        ],
        key=lambda e: e["mtime"],
        reverse=True
    )
    return {"commits": commits}


# Hub - get commits
@app.route("/commits/<owner>/<repo>/<commit_hash>", methods=['GET'])
def commits_get(owner, repo, commit_hash):
    repo_dir = os.path.join(data_dir, "hub", owner, repo)
    commit_path = os.path.join(repo_dir, commit_hash)
    if not os.path.isfile(commit_path):
        abort(404)
    with open(commit_path, "rb") as fr:
        manifest = json.loads(fr.read())
    return {"manifest": manifest}


# Hub - post commits
@app.route(
    "/commits/<owner>/<repo>", methods=['POST'])
def commits_post(owner, repo):
    manifest = request.json["manifest"]
    data = json.dumps(manifest).encode()
    commit_hash = hashlib.sha256(data).hexdigest()[:8]

    repo_dir = os.path.join(data_dir, "hub", owner, repo)
    with open(os.path.join(repo_dir, commit_hash), "wb") as fw:
        fw.write(data)

    return {"commit": {"commit_hash": commit_hash}}


# Trace - create runs
@app.route("/runs", methods=['POST'])
def runs_create():
    runs_dir = os.path.join(data_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    run_id = request.json["id"]
    run_path = os.path.join(runs_dir, run_id)
    with open(run_path, "w") as fw:
        fw.write(json.dumps(request.json))
    return {}


# Trace - update runs
@app.route("/runs/<run_id>", methods=["PATCH"])
def runs_update(run_id):
    run_path = os.path.join(data_dir, "runs", run_id)

    exist_check = False
    for trial in range(3):
        if os.path.isfile(run_path):
            exist_check = True
            break
        time.sleep(0.1)
    if not exist_check:
        abort(404)

    with open(run_path, "r+") as fw:
        fcntl.flock(fw, fcntl.LOCK_EX)
        original_json_data = json.loads(fw.read())
        update_json_data = request.json
        new_json_data = dict(original_json_data, **update_json_data)

        fw.truncate(0)
        fw.seek(os.SEEK_SET)
        fw.write(json.dumps(new_json_data))
    return {}


# Settings - get settings
@app.route("/settings", methods=['GET'])
def settings_get():
    return {"tenant_handle": repo_owner}


if __name__ == "__main__":
    app.run(
        host=os.environ.get("LANGSMITH_MOCK_HOST", "0.0.0.0"),
        port=os.environ.get("LANGSMITH_MOCK_PORT", 3000)
    )
