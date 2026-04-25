#!/usr/bin/env python3
"""
nexus.py — Echo Universe Transitive Communication Mesh
Maps every direct and indirect connection across the entire estate.
Enables signal routing through N degrees of separation.

Mathematical model:
  G = (V, E) where:
    V = all nodes (repos, agents, services, workflows)
    E = all directed edges (dispatch, import, deploy, API call)

  For any source node s and target node t:
    path(s, t) = BFS/Dijkstra over G
    transitive_reach(s) = all nodes reachable from s
    influence_score(v) = PageRank(v) over G

  Signal routing:
    route(signal, s, t) = path(s, t) → emit signal at each hop

Author: Manus AI | ∇θ Nathan Poinsette
Version: 1.0.0
"""
import json
import os
import hashlib
import subprocess
import time
from collections import defaultdict, deque
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

ECHO_DIR   = Path(".echo")
NEXUS_MAP  = ECHO_DIR / "nexus_map.json"
COORD_LOG  = Path("coordination_log.jsonl")
TOKEN      = os.environ.get("GITHUB_TOKEN", "")
OWNER      = "onlyecho822-source"
NOW        = lambda: datetime.now(timezone.utc).isoformat() + "Z"
KAPPA      = 0.618034

# ── Node Types ────────────────────────────────────────────────────────────────
NODE_REPO     = "repo"
NODE_AGENT    = "agent"
NODE_SERVICE  = "service"
NODE_WORKFLOW = "workflow"
NODE_HUMAN    = "human"

# ── Edge Types ────────────────────────────────────────────────────────────────
EDGE_DISPATCH  = "repository_dispatch"   # GitHub Actions dispatch
EDGE_IMPORT    = "python_import"         # Python module import
EDGE_DEPLOY    = "file_deploy"           # File pushed to repo
EDGE_API       = "api_call"              # External API call
EDGE_COORD     = "coordination_log"      # Coordination log entry
EDGE_AGENT     = "agent_registry"        # Agent registry reference
EDGE_WORKFLOW  = "workflow_trigger"      # Workflow trigger


class Node:
    def __init__(self, node_id: str, node_type: str, metadata: dict = None):
        self.id       = node_id
        self.type     = node_type
        self.metadata = metadata or {}
        self.edges_out: list["Edge"] = []
        self.edges_in:  list["Edge"] = []

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "metadata": self.metadata,
            "out_degree": len(self.edges_out),
            "in_degree": len(self.edges_in),
        }


class Edge:
    def __init__(self, source: str, target: str, edge_type: str,
                 weight: float = 1.0, metadata: dict = None):
        self.source   = source
        self.target   = target
        self.type     = edge_type
        self.weight   = weight
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "weight": self.weight,
        }


class NexusGraph:
    """
    The full transitive communication graph of the Echo Universe.
    Nodes: repos, agents, services, workflows, humans.
    Edges: dispatch, import, deploy, API, coordination, agent registry.
    """

    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge]      = []
        self._adj: dict[str, list[str]] = defaultdict(list)   # adjacency list
        self._radj: dict[str, list[str]] = defaultdict(list)  # reverse adjacency

    # ── Graph Construction ────────────────────────────────────────────────────
    def add_node(self, node_id: str, node_type: str, metadata: dict = None) -> Node:
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, node_type, metadata)
        else:
            if metadata:
                self.nodes[node_id].metadata.update(metadata)
        return self.nodes[node_id]

    def add_edge(self, source: str, target: str, edge_type: str,
                 weight: float = 1.0, metadata: dict = None):
        if source not in self.nodes:
            self.add_node(source, NODE_REPO)
        if target not in self.nodes:
            self.add_node(target, NODE_REPO)
        e = Edge(source, target, edge_type, weight, metadata)
        self.edges.append(e)
        self.nodes[source].edges_out.append(e)
        self.nodes[target].edges_in.append(e)
        if target not in self._adj[source]:
            self._adj[source].append(target)
        if source not in self._radj[target]:
            self._radj[target].append(source)

    # ── Graph Algorithms ──────────────────────────────────────────────────────
    def bfs(self, start: str, max_depth: int = 999) -> dict[str, int]:
        """
        BFS from start node. Returns {node_id: depth} for all reachable nodes.
        """
        if start not in self.nodes:
            return {}
        visited = {start: 0}
        queue   = deque([(start, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor in self._adj.get(node, []):
                if neighbor not in visited:
                    visited[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))
        return visited

    def shortest_path(self, source: str, target: str) -> Optional[list[str]]:
        """
        BFS shortest path from source to target.
        Returns list of node IDs or None if no path.
        """
        if source not in self.nodes or target not in self.nodes:
            return None
        if source == target:
            return [source]
        visited = {source: None}
        queue   = deque([source])
        while queue:
            node = queue.popleft()
            for neighbor in self._adj.get(node, []):
                if neighbor not in visited:
                    visited[neighbor] = node
                    if neighbor == target:
                        # Reconstruct path
                        path = []
                        cur = target
                        while cur is not None:
                            path.append(cur)
                            cur = visited[cur]
                        return list(reversed(path))
                    queue.append(neighbor)
        return None

    def transitive_reach(self, start: str) -> set[str]:
        """All nodes reachable from start (excluding start itself)."""
        reached = self.bfs(start)
        reached.pop(start, None)
        return set(reached.keys())

    def pagerank(self, damping: float = 0.85, iterations: int = 50) -> dict[str, float]:
        """
        Compute PageRank for all nodes.
        Returns {node_id: score}.
        """
        n = len(self.nodes)
        if n == 0:
            return {}
        rank = {nid: 1.0 / n for nid in self.nodes}
        for _ in range(iterations):
            new_rank = {}
            for nid in self.nodes:
                incoming = self._radj.get(nid, [])
                score = (1.0 - damping) / n
                for src in incoming:
                    out_count = len(self._adj.get(src, [])) or 1
                    score += damping * rank[src] / out_count
                new_rank[nid] = score
            rank = new_rank
        return rank

    def influence_score(self, node_id: str) -> float:
        """
        Combined influence = κ * pagerank_normalized + (1-κ) * out_degree_normalized
        """
        pr = self.pagerank()
        max_pr = max(pr.values()) if pr else 1.0
        pr_norm = pr.get(node_id, 0.0) / max_pr if max_pr > 0 else 0.0
        max_out = max(len(self._adj.get(n, [])) for n in self.nodes) if self.nodes else 1
        out_norm = len(self._adj.get(node_id, [])) / max_out if max_out > 0 else 0.0
        return KAPPA * pr_norm + (1.0 - KAPPA) * out_norm

    def strongly_connected_components(self) -> list[set[str]]:
        """Kosaraju's algorithm for SCCs."""
        visited = set()
        finish_order = []

        def dfs1(v):
            stack = [(v, iter(self._adj.get(v, [])))]
            while stack:
                node, neighbors = stack[-1]
                try:
                    nb = next(neighbors)
                    if nb not in visited:
                        visited.add(nb)
                        stack.append((nb, iter(self._adj.get(nb, []))))
                except StopIteration:
                    finish_order.append(node)
                    stack.pop()

        for node in self.nodes:
            if node not in visited:
                visited.add(node)
                dfs1(node)

        visited2 = set()
        components = []

        def dfs2(v, comp):
            stack = [v]
            while stack:
                node = stack.pop()
                comp.add(node)
                for nb in self._radj.get(node, []):
                    if nb not in visited2:
                        visited2.add(nb)
                        stack.append(nb)

        for node in reversed(finish_order):
            if node not in visited2:
                visited2.add(node)
                comp = {node}
                dfs2(node, comp)
                components.append(comp)

        return components

    # ── Signal Routing ────────────────────────────────────────────────────────
    def route_signal(self, signal: dict, source: str, target: str) -> dict:
        """
        Route a signal from source to target through the graph.
        Returns routing result with path, hops, and signal copies.
        """
        path = self.shortest_path(source, target)
        if not path:
            return {
                "status": "UNROUTABLE",
                "source": source,
                "target": target,
                "path": None,
                "hops": 0,
            }
        result = {
            "status": "ROUTED",
            "source": source,
            "target": target,
            "path": path,
            "hops": len(path) - 1,
            "signal": signal,
            "timestamp": NOW(),
            "idem_key": hashlib.sha256(
                f"{source}{target}{signal.get('type','')}{NOW()}".encode()
            ).hexdigest()[:16],
        }
        return result

    def broadcast(self, signal: dict, source: str, max_depth: int = 3) -> dict:
        """
        Broadcast a signal from source to all reachable nodes within max_depth hops.
        Returns broadcast result with all reached nodes.
        """
        reached = self.bfs(source, max_depth=max_depth)
        reached.pop(source, None)
        return {
            "status": "BROADCAST",
            "source": source,
            "reached": list(reached.keys()),
            "reach_count": len(reached),
            "max_depth": max_depth,
            "signal": signal,
            "timestamp": NOW(),
        }

    # ── Serialization ─────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        pr = self.pagerank()
        sccs = self.strongly_connected_components()
        return {
            "schema_version": "1.0.0",
            "generated_at": NOW(),
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "scc_count": len(sccs),
                "largest_scc": max((len(s) for s in sccs), default=0),
            },
            "nodes": {nid: {**n.to_dict(), "pagerank": round(pr.get(nid, 0.0), 6)}
                      for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "top_influencers": sorted(
                [{"id": nid, "score": round(self.influence_score(nid), 6)}
                 for nid in self.nodes],
                key=lambda x: x["score"], reverse=True
            )[:20],
        }

    def save(self, path: Path = NEXUS_MAP):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path = NEXUS_MAP) -> "NexusGraph":
        g = cls()
        if not path.exists():
            return g
        with open(path) as f:
            data = json.load(f)
        for nid, nd in data.get("nodes", {}).items():
            g.add_node(nid, nd.get("type", NODE_REPO), nd.get("metadata", {}))
        for ed in data.get("edges", []):
            g.add_edge(ed["source"], ed["target"], ed["type"],
                       ed.get("weight", 1.0), ed.get("metadata", {}))
        return g


# ── Graph Builder ─────────────────────────────────────────────────────────────
def build_from_github(token: str = TOKEN, owner: str = OWNER) -> NexusGraph:
    """
    Build the full nexus graph from the live GitHub estate.
    Discovers: repos, workflows, dispatch edges, agent registry, external services.
    """
    g = NexusGraph()

    def api(path):
        r = subprocess.run(
            ["curl", "-s", "-H", f"Authorization: token {token}",
             "-H", "Accept: application/vnd.github+json",
             f"https://api.github.com{path}"],
            capture_output=True, text=True, timeout=20
        )
        try: return json.loads(r.stdout)
        except: return {}

    def get_file(repo, path):
        import base64
        r = api(f"/repos/{owner}/{repo}/contents/{path}")
        if isinstance(r, dict) and "content" in r:
            return base64.b64decode(r["content"]).decode("utf-8", "replace")
        return None

    # Add known external service nodes
    for svc in ["github.com", "railway.app", "fly.io", "slack.com",
                "openai.com", "stripe.com", "redis.io"]:
        g.add_node(svc, NODE_SERVICE, {"external": True})

    # Add known agent nodes
    for agent in ["manus-ai", "claude", "nabla-theta"]:
        g.add_node(agent, NODE_AGENT, {"trust": "trusted_external"})

    # Add human operator
    g.add_node("nathan-poinsette", NODE_HUMAN, {"role": "operator", "symbol": "∇θ"})
    g.add_edge("nathan-poinsette", "manus-ai",    EDGE_AGENT, 1.0)
    g.add_edge("nathan-poinsette", "claude",       EDGE_AGENT, 1.0)
    g.add_edge("nathan-poinsette", "nabla-theta",  EDGE_AGENT, 1.0)

    # Enumerate all repos via authenticated user endpoint
    repos = []
    page = 1
    while True:
        data = api(f"/user/repos?affiliation=owner&per_page=100&page={page}")
        if not isinstance(data, list) or not data:
            break
        for r in data:
            owner_login = r.get("owner", {}).get("login", "").lower()
            if owner_login == owner.lower():
                repos.append(r)
        if len(data) < 100:
            break
        page += 1
    # Also try org endpoint as fallback
    if not repos:
        page = 1
        while True:
            data = api(f"/orgs/{owner}/repos?type=all&per_page=100&page={page}")
            if not isinstance(data, list) or not data:
                break
            repos.extend(data)
            if len(data) < 100:
                break
            page += 1

    print(f"  Building nexus graph from {len(repos)} repos...")

    for repo in repos:
        name     = repo["name"]
        archived = repo.get("archived", False)
        lang     = repo.get("language", "unknown")
        stars    = repo.get("stargazers_count", 0)
        forks    = repo.get("forks_count", 0)
        topics   = repo.get("topics", [])

        g.add_node(name, NODE_REPO, {
            "archived": archived,
            "language": lang,
            "stars": stars,
            "forks": forks,
            "topics": topics,
            "default_branch": repo.get("default_branch", "main"),
            "private": repo.get("private", False),
        })

        # Edge: operator owns all repos
        g.add_edge("nathan-poinsette", name, EDGE_DEPLOY, 1.0)

        # Edge: agents deployed to this repo
        g.add_edge("manus-ai", name, EDGE_DEPLOY, 1.0)
        g.add_edge("claude",   name, EDGE_DEPLOY, 0.8)

        # Discover workflow dispatch edges
        wfs = api(f"/repos/{owner}/{name}/actions/workflows")
        for wf in wfs.get("workflows", []):
            wf_name = wf.get("name", "")
            wf_id   = f"{name}/{wf_name}"
            g.add_node(wf_id, NODE_WORKFLOW, {"repo": name, "workflow": wf_name})
            g.add_edge(name, wf_id, EDGE_WORKFLOW, 1.0)

            # Dispatch edges: workflows that send repository_dispatch
            if any(k in wf_name.lower() for k in
                   ["dispatch", "motor", "kraken", "propagate", "sync", "nexus"]):
                g.add_edge(wf_id, "echo-kraken-motor", EDGE_DISPATCH, 1.0)
                g.add_edge(wf_id, "echo-kraken-brain", EDGE_DISPATCH, 0.9)

            # Health check workflows connect to external services
            if any(k in wf_name.lower() for k in ["health", "deploy", "fly", "railway"]):
                g.add_edge(wf_id, "fly.io",      EDGE_API, 0.7)
                g.add_edge(wf_id, "railway.app", EDGE_API, 0.7)

            # Slack notification workflows
            if "slack" in wf_name.lower():
                g.add_edge(wf_id, "slack.com", EDGE_API, 1.0)

        # Discover .echo/agent_registry.json edges
        registry = get_file(name, ".echo/agent_registry.json")
        if registry:
            try:
                reg = json.loads(registry)
                for agent_entry in reg.get("agents", []):
                    agent_id = agent_entry.get("id", "")
                    if agent_id:
                        if agent_id not in g.nodes:
                            g.add_node(agent_id, NODE_AGENT)
                        g.add_edge(name, agent_id, EDGE_AGENT, 1.0)
            except Exception:
                pass

        # Discover Python import edges from agent.py
        agent_py = get_file(name, "agent.py")
        if agent_py:
            for line in agent_py.split("\n"):
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    for mod in ["biology", "genome", "metabolism", "heartbeat", "nexus"]:
                        if mod in line:
                            g.add_edge(name, f"{name}/{mod}.py", EDGE_IMPORT, 1.0)

        # Core architecture edges
        if name in ("echo-core", "echo-kraken-brain", "echo-kraken-motor"):
            for other in repos:
                other_name = other["name"]
                if other_name != name and not other.get("archived"):
                    g.add_edge(name, other_name, EDGE_DISPATCH, 0.5)

        time.sleep(0.05)  # rate limit

    # Coordination log edges (echo-core → all)
    g.add_edge("echo-core",         "echo-kraken-brain",  EDGE_COORD, 1.0)
    g.add_edge("echo-kraken-brain", "echo-kraken-motor",  EDGE_COORD, 1.0)
    g.add_edge("echo-kraken-motor", "echo-core",          EDGE_COORD, 1.0)
    g.add_edge("manus-ai",          "echo-core",          EDGE_COORD, 1.0)
    g.add_edge("claude",            "echo-core",          EDGE_COORD, 1.0)

    return g


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    os.chdir(Path(__file__).parent)

    print(f"\n{'='*65}")
    print(f"  ECHO NEXUS — Transitive Communication Mesh Builder")
    print(f"  {NOW()}")
    print(f"{'='*65}\n")

    if not TOKEN:
        print("ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    print("Building graph from live GitHub estate...")
    g = build_from_github()

    print(f"\nGraph stats:")
    print(f"  Nodes:  {len(g.nodes)}")
    print(f"  Edges:  {len(g.edges)}")

    sccs = g.strongly_connected_components()
    print(f"  SCCs:   {len(sccs)} | Largest: {max(len(s) for s in sccs)}")

    print(f"\nTop 10 influencers (κ-weighted PageRank + out-degree):")
    pr = g.pagerank()
    influencers = sorted(
        [(nid, g.influence_score(nid)) for nid in g.nodes],
        key=lambda x: x[1], reverse=True
    )[:10]
    for rank, (nid, score) in enumerate(influencers, 1):
        node = g.nodes[nid]
        reach = len(g.transitive_reach(nid))
        print(f"  {rank:2d}. {nid:<45} score={score:.4f} reach={reach}")

    # Test routing
    print(f"\nSignal routing test:")
    test_signal = {"type": "test.nexus", "payload": {"msg": "hello from nexus"}}
    result = g.route_signal(test_signal, "echo-core", "echo-harmonic-singularity")
    print(f"  echo-core → echo-harmonic-singularity: {result['status']} | {result['hops']} hops | path={result['path']}")

    # Test broadcast
    bcast = g.broadcast(test_signal, "echo-kraken-brain", max_depth=2)
    print(f"  Broadcast from echo-kraken-brain (depth=2): reached {bcast['reach_count']} nodes")

    # Save
    out = ECHO_DIR / "nexus_map.json"
    g.save(out)
    print(f"\nNexus map saved to {out}")
    print(f"  File size: {out.stat().st_size / 1024:.1f} KB")
    print(f"\n{'='*65}")
    print(f"  NEXUS BUILD COMPLETE")
    print(f"{'='*65}\n")
