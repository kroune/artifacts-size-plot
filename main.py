import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

import matplotlib.pyplot as plt
import requests

GITHUB_TOKEN = os.environ['INPUT_GITHUB_TOKEN']
REPO_OWNER = os.environ['INPUT_REPOSITORY_OWNER']
REPO_NAME = os.environ['INPUT_REPOSITORY_NAME']

url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/artifacts?per_page=100'
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

@dataclass
class WorkflowRun:
    id: int
    repository_id: int
    head_repository_id: int
    head_branch: str
    head_sha: str

    @classmethod
    def from_json(cls, data: dict) -> 'WorkflowRun':
        return cls(
            id=data['id'],
            repository_id=data['repository_id'],
            head_repository_id=data['head_repository_id'],
            head_branch=data['head_branch'],
            head_sha=data['head_sha']
        )


@dataclass
class Artifact:
    id: int
    node_id: str
    name: str
    size_in_bytes: int
    url: str
    archive_download_url: str
    expired: bool
    created_at: datetime
    expires_at: datetime
    updated_at: datetime
    workflow_run: Optional[WorkflowRun]

    @classmethod
    def from_json(cls, data: dict) -> 'Artifact':
        workflow_run_data = data.get('workflow_run')
        workflow_run = WorkflowRun.from_json(workflow_run_data) if workflow_run_data else None

        return cls(
            id=data['id'],
            node_id=data['node_id'],
            name=data['name'],
            size_in_bytes=data['size_in_bytes'],
            url=data['url'],
            archive_download_url=data['archive_download_url'],
            expired=data['expired'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            expires_at=datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            workflow_run=workflow_run
        )


def bytes_to_megabytes(size_in_bytes: int) -> float:
    return size_in_bytes / (1024 * 1024)


def get_artifacts() -> List[Artifact]:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return [Artifact.from_json(artifact) for artifact in data['artifacts']]
    else:
        print(f"Failed to fetch artifacts. Status code: {response.status_code}")
        print(response.text)
        exit(-1)


# Функция для построения и сохранения графиков
def plot_artifact_sizes(artifacts_to_size_map: Dict[str, List[int]]):
    defaultColor = (115 / 256, 65 / 256, 220 / 256)
    defaultColor2 = (175 / 256, 150 / 256, 230 / 256)
    for name, sizes in artifacts_to_size_map.items():
        sizes_mb = [bytes_to_megabytes(sizes[0] - size) for size in sizes]
        plt.subplots(figsize=(10, 4))
        plt.plot(sizes_mb, color=defaultColor)
        plt.title(f'{name.removeprefix("NineMensMorris-").removesuffix("-artifact")}', color=defaultColor)
        plt.xlabel('Artifact Index', color=defaultColor)
        some_range = range(0, len(sizes), 1)
        plt.xticks(some_range)
        plt.axhline(0, color=defaultColor2, linewidth=0.8, linestyle='--')
        plt.ylabel('Size (MB)', color=defaultColor)
        plt.grid(False)
        plt.tick_params(labelcolor=defaultColor)
        plt.gca().spines['top'].set_edgecolor(defaultColor)
        plt.gca().spines['bottom'].set_edgecolor(defaultColor)
        plt.gca().spines['left'].set_edgecolor(defaultColor)
        plt.gca().spines['right'].set_edgecolor(defaultColor)
        plt.savefig(f'plot-artifacts/{name}_sizes.png', transparent=True)
        plt.close()


artifactsToSizeMap: Dict[str, list[int]] = {}
artifacts = get_artifacts()
for artifact in artifacts:
    if artifact.name not in artifactsToSizeMap:
        artifactsToSizeMap[artifact.name] = []
    artifactsToSizeMap[artifact.name].append(artifact.size_in_bytes)
for name in artifactsToSizeMap:
    print(f'Showing info about {name} artifacts')
    artifactsSizes = artifactsToSizeMap[name]
    for size in artifactsSizes:
        print(f'Size: {size} bytes')
    print("")
    print("")
    print("")
subprocess.run(["mkdir", "plot-artifacts"])
plot_artifact_sizes(artifactsToSizeMap)
home = os.environ['HOME']
subprocess.run(["cp", "-rf", "plot-artifacts/", home])
