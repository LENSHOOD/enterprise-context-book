"""Streaming SQLite model for a complete Linux source tree."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import time
from collections import Counter
from pathlib import Path

from .engine import CALL_RE, CONTROL_WORDS, _commit, _function_spans, _line


CODE_SUFFIXES = {".c", ".h"}
DOC_SUFFIXES = {".rst", ".md", ".txt"}
FULL_TYPE_RE = re.compile(r"(?m)^\s*(?:struct|enum)\s+([A-Za-z_]\w*)[^;\n]*\{")


def subsystem(path: str) -> str:
    parts = path.split("/")
    if not parts:
        return "root"
    if parts[0] in {"drivers", "fs", "net", "sound", "arch"} and len(parts) > 1:
        return f"{parts[0]}/{parts[1]}"
    if parts[0] == "Documentation" and len(parts) > 1:
        return f"Documentation/{parts[1]}"
    return parts[0]


def _tracked_files(repo: Path) -> list[str]:
    if not (repo / ".git").exists():
        return sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file())
    try:
        output = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "-z"], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        return sorted(item.decode("utf-8", errors="replace") for item in output.split(b"\0") if item)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted(path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file())


def _schema(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    CREATE TABLE manifest (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE nodes (
      id INTEGER PRIMARY KEY,
      stable_id TEXT NOT NULL UNIQUE,
      kind TEXT NOT NULL,
      name TEXT NOT NULL,
      path TEXT NOT NULL,
      subsystem TEXT NOT NULL,
      line INTEGER NOT NULL,
      citation TEXT NOT NULL,
      content TEXT NOT NULL
    );
    CREATE TABLE raw_calls (
      source_id INTEGER NOT NULL,
      target_name TEXT NOT NULL,
      evidence TEXT NOT NULL,
      UNIQUE(source_id, target_name)
    );
    CREATE TABLE edges (
      source_id INTEGER NOT NULL,
      edge_type TEXT NOT NULL,
      target_id INTEGER,
      target_name TEXT,
      certainty TEXT NOT NULL,
      evidence TEXT,
      UNIQUE(source_id, edge_type, target_id, target_name)
    );
    CREATE VIRTUAL TABLE node_fts USING fts5(name, path, content, content='nodes', content_rowid='id');
    CREATE INDEX nodes_name_idx ON nodes(name);
    CREATE INDEX nodes_subsystem_idx ON nodes(subsystem);
    CREATE INDEX edges_source_idx ON edges(source_id);
    CREATE INDEX edges_target_idx ON edges(target_id);
    """)


def _insert_node(connection: sqlite3.Connection, values: tuple) -> int:
    cursor = connection.execute(
        "INSERT OR IGNORE INTO nodes(stable_id,kind,name,path,subsystem,line,citation,content) VALUES(?,?,?,?,?,?,?,?)",
        values,
    )
    if cursor.lastrowid:
        return int(cursor.lastrowid)
    return int(connection.execute("SELECT id FROM nodes WHERE stable_id=?", (values[0],)).fetchone()[0])


def ingest_full(repo: Path, ref: str, database: Path, include_docs: bool = True) -> dict:
    repo, database = repo.resolve(), database.resolve()
    commit, started = _commit(repo, ref), time.monotonic()
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.exists():
        raise FileExistsError(f"database already exists: {database}")
    connection = sqlite3.connect(database)
    _schema(connection)
    counts = Counter()
    paths = _tracked_files(repo)

    for index, relative in enumerate(paths, start=1):
        path, suffix = repo / relative, Path(relative).suffix
        if suffix not in CODE_SUFFIXES and not (include_docs and relative.startswith("Documentation/") and suffix in DOC_SUFFIXES):
            continue
        if not path.is_file():
            counts["missing_worktree"] += 1
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        group = subsystem(relative)
        citation = f"code://linux/kernel@{commit}/{relative}#file:L1"
        file_id = _insert_node(connection, (
            f"file:{relative}", "file" if suffix in CODE_SUFFIXES else "document",
            path.name, relative, group, 1, citation, text[:2000],
        ))
        counts["files"] += 1
        if suffix in CODE_SUFFIXES:
            for type_name in FULL_TYPE_RE.findall(text):
                offset = text.find(type_name)
                line = _line(text, offset)
                type_id = _insert_node(connection, (
                    f"type:{relative}#{type_name}:L{line}", "type", type_name, relative,
                    group, line, f"code://linux/kernel@{commit}/{relative}#{type_name}:L{line}",
                    f"type {type_name} defined in {relative}",
                ))
                connection.execute(
                    "INSERT OR IGNORE INTO edges VALUES(?,?,?,?,?,?)",
                    (file_id, "DEFINES", type_id, None, "syntax", citation),
                )
                counts["types"] += 1
            for name, start, end, body in _function_spans(text):
                if name in CONTROL_WORDS:
                    continue
                line = _line(text, start)
                symbol_citation = f"code://linux/kernel@{commit}/{relative}#{name}:L{line}"
                symbol_id = _insert_node(connection, (
                    f"symbol:{relative}#{name}:L{line}", "function", name, relative,
                    group, line, symbol_citation, text[start:min(end, start + 2000)],
                ))
                connection.execute(
                    "INSERT OR IGNORE INTO edges VALUES(?,?,?,?,?,?)",
                    (file_id, "DEFINES", symbol_id, None, "syntax", symbol_citation),
                )
                for called in set(CALL_RE.findall(body)) - CONTROL_WORDS:
                    connection.execute(
                        "INSERT OR IGNORE INTO raw_calls VALUES(?,?,?)",
                        (symbol_id, called, symbol_citation),
                    )
                counts["functions"] += 1
        if index % 500 == 0:
            connection.commit()

    scan_seconds = round(time.monotonic() - started, 3)
    connection.execute("INSERT INTO node_fts(rowid,name,path,content) SELECT id,name,path,content FROM nodes")
    connection.commit()
    # Pre-aggregate names once. Correlated COUNT per call is prohibitively slow at kernel scale.
    connection.execute("""
      CREATE TEMP TABLE function_name_resolution AS
      SELECT name, COUNT(*) AS target_count, MIN(id) AS target_id
      FROM nodes WHERE kind='function' GROUP BY name
    """)
    connection.execute("CREATE INDEX temp.function_name_resolution_idx ON function_name_resolution(name)")
    # Resolve only globally unique names. Ambiguous and missing targets stay explicit.
    connection.execute("""
      INSERT OR IGNORE INTO edges(source_id,edge_type,target_id,target_name,certainty,evidence)
      SELECT r.source_id, 'CALLS_NAME_RESOLVED', x.target_id, NULL, 'name-resolved', r.evidence
      FROM raw_calls r JOIN function_name_resolution x ON x.name=r.target_name
      WHERE x.target_count=1
    """)
    connection.execute("""
      INSERT OR IGNORE INTO edges(source_id,edge_type,target_id,target_name,certainty,evidence)
      SELECT r.source_id, 'CALLS_CANDIDATE', NULL, r.target_name, 'syntax-candidate', r.evidence
      FROM raw_calls r LEFT JOIN function_name_resolution x ON x.name=r.target_name
      WHERE x.target_count IS NULL OR x.target_count != 1
    """)
    elapsed = round(time.monotonic() - started, 3)
    stats = {
        "schema": "linux-full-kb@1", "repository": str(repo), "ref": ref,
        "commit": commit, "mode": "sqlite-syntax-only", "include_docs": include_docs,
        "scan_seconds": scan_seconds,
        "elapsed_seconds": elapsed,
        "counts": {
            "tracked_paths": len(paths),
            "files": connection.execute("SELECT COUNT(*) FROM nodes WHERE kind IN ('file','document')").fetchone()[0],
            "functions": connection.execute("SELECT COUNT(*) FROM nodes WHERE kind='function'").fetchone()[0],
            "types": connection.execute("SELECT COUNT(*) FROM nodes WHERE kind='type'").fetchone()[0],
            "nodes": connection.execute("SELECT COUNT(*) FROM nodes").fetchone()[0],
            "edges": connection.execute("SELECT COUNT(*) FROM edges").fetchone()[0],
            "resolved_calls": connection.execute("SELECT COUNT(*) FROM edges WHERE edge_type='CALLS_NAME_RESOLVED'").fetchone()[0],
            "candidate_calls": connection.execute("SELECT COUNT(*) FROM edges WHERE edge_type='CALLS_CANDIDATE'").fetchone()[0],
            "missing_worktree": counts["missing_worktree"],
        },
    }
    for key, value in stats.items():
        connection.execute("INSERT INTO manifest VALUES(?,?)", (key, json.dumps(value)))
    connection.commit()
    connection.execute("PRAGMA optimize")
    connection.close()
    return stats


def query_full(database: Path, question: str, limit: int = 10, subsystem_filter: str | None = None) -> dict:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    terms = [term for term in CALL_RE.findall(question + "(") if term not in CONTROL_WORDS]
    # CALL_RE is not a tokenizer; use conservative identifier extraction for FTS.
    terms = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", question)
    expression = " OR ".join(f'"{term}"' for term in terms) or '"linux"'
    sql = """
      SELECT n.*, bm25(node_fts, 8.0, 3.0, 1.0) AS rank
      FROM node_fts JOIN nodes n ON n.id=node_fts.rowid
      WHERE node_fts MATCH ?
        AND n.name NOT IN ('if','for','while','switch','return','sizeof','defined')
    """
    params: list[object] = [expression]
    if subsystem_filter:
        sql += " AND n.subsystem=?"
        params.append(subsystem_filter)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    hits = [dict(row) for row in connection.execute(sql, params)]
    ids = [hit["id"] for hit in hits]
    edges = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        edges = [dict(row) for row in connection.execute(
            f"SELECT * FROM edges WHERE source_id IN ({placeholders}) LIMIT 200", ids
        )]
    manifest = {row["key"]: json.loads(row["value"]) for row in connection.execute("SELECT * FROM manifest")}
    connection.close()
    return {"question": question, "subsystem": subsystem_filter, "manifest": manifest, "hits": hits, "edges": edges}


def report_full(database: Path, limit: int = 40) -> dict:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    manifest = {row["key"]: json.loads(row["value"]) for row in connection.execute("SELECT * FROM manifest")}
    subsystems = [dict(row) for row in connection.execute("""
      SELECT subsystem,
             SUM(kind IN ('file','document')) AS files,
             SUM(kind='function') AS functions,
             SUM(kind='type') AS types
      FROM nodes GROUP BY subsystem ORDER BY files DESC LIMIT ?
    """, (limit,))]
    database_bytes = database.stat().st_size
    connection.close()
    return {"manifest": manifest, "database_bytes": database_bytes, "top_subsystems": subsystems}
