"""Generate the MkDocs skill and agent catalog from configured source roots.

Standalone pre-build script. Reads docs/catalog-sources.yml to discover plugin
(or project-local .claude) directories whose skills/ and agents/ subfolders
should appear in the catalog. Writes real markdown files into docs/<locale>/
for every configured locale so that mkdocs-static-i18n treats them as regular
locale-specific pages. The generated files are .gitignored and must be
regenerated before every docs build (run via `task docs:catalog`).

Fails with a clear error on malformed frontmatter so the catalog can never be
silently broken.

Spec: https://github.com/nolte/claude-shared/blob/main/spec/claude/skill-agent-catalog/en.md
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

SOURCES_FILE = Path("docs/catalog-sources.yml")
DOCS_DIR = Path("docs")
TAG_INDEX_PATH = "tags.md"
# Emit generated pages under every locale the i18n plugin builds, so that
# mkdocs-static-i18n (docs_structure: folder) treats them as navigable
# pages. Content is language-neutral per spec.
LOCALES = ("de", "en")


class CatalogError(RuntimeError):
    """Raised when an artifact has invalid frontmatter or the sources file is broken."""


@dataclass(frozen=True)
class Source:
    name: str
    local: Path
    skills_path: str
    agents_path: str
    repo_url: str
    branch: str


@dataclass(frozen=True)
class Artifact:
    kind: str  # "skill" | "agent"
    source: Source
    name: str
    description: str
    distribution: str | None
    tags: tuple[str, ...]
    body: str
    rel_source_path: str


_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)

_KV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


def _load_sources(repo_root: Path) -> list[Source]:
    cfg_path = repo_root / SOURCES_FILE
    if not cfg_path.exists():
        raise CatalogError(f"{cfg_path}: catalog-sources.yml not found")
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    entries = data.get("sources") or []
    if not entries:
        raise CatalogError(f"{cfg_path}: no sources declared")
    sources: list[Source] = []
    for entry in entries:
        try:
            sources.append(
                Source(
                    name=entry["name"],
                    local=(repo_root / entry["local"]).resolve(),
                    skills_path=entry.get("skills_path", "skills"),
                    agents_path=entry.get("agents_path", "agents"),
                    repo_url=entry["repo_url"].rstrip("/"),
                    branch=entry.get("branch", "main"),
                )
            )
        except KeyError as exc:
            raise CatalogError(
                f"{cfg_path}: source entry missing required key {exc!s}: {entry!r}"
            ) from exc
    return sources


def _parse_frontmatter_block(block: str, path: Path) -> dict:
    """Parse Claude Code frontmatter.

    Claude Code's frontmatter looks like YAML but its descriptions routinely
    contain unquoted colons ("Read-only: ...", "URL: https://..."). Standard
    YAML parsers reject that. We parse line-oriented instead: each top-level
    key maps to the rest of its line as a plain string; indented `- ` lines
    or inline `[a, b, c]` values are parsed as lists for keys like `tags`.
    """
    result: dict[str, object] = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        match = _KV_LINE_RE.match(line)
        if not match:
            raise CatalogError(f"{path}: cannot parse frontmatter line: {line!r}")
        key, value = match.group(1), match.group(2).rstrip()
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            block_lines: list[str] = []
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].startswith((" ", "\t"))):
                block_lines.append(lines[j])
                j += 1
            while block_lines and not block_lines[-1].strip():
                block_lines.pop()
            if block_lines:
                indent = min(
                    len(l) - len(l.lstrip(" \t")) for l in block_lines if l.strip()
                )
                dedented = [l[indent:] if l.strip() else "" for l in block_lines]
            else:
                dedented = []
            if value.startswith(">"):
                result[key] = " ".join(l.strip() for l in dedented if l.strip())
            else:
                result[key] = "\n".join(dedented)
            i = j
            continue
        items: list[str] = []
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or lines[j].startswith((" ", "\t"))):
            stripped = lines[j].strip()
            if stripped.startswith("- "):
                items.append(stripped[2:].strip().strip("\"'"))
            elif stripped == "":
                pass
            else:
                break
            j += 1
        if items:
            result[key] = items
            i = j
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [t.strip().strip("\"'") for t in inner.split(",")] if inner else []
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            result[key] = value
        i += 1
    return result


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise CatalogError(f"{path}: no YAML frontmatter block")
    return _parse_frontmatter_block(match.group("fm"), path), match.group("body").lstrip()


def _require_str(value: object, field: str, path: Path, source: Source) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(
            f"{path} (source `{source.name}`): missing or invalid `{field}` field"
        )
    return value


def _tags(value: object, path: Path, source: Source) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
        raise CatalogError(
            f"{path} (source `{source.name}`): `tags` must be a list of strings"
        )
    return tuple(value)


def _collect_skills(source: Source) -> list[Artifact]:
    base = source.local / source.skills_path
    if not base.exists():
        return []
    out: list[Artifact] = []
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        skill_md = folder / "SKILL.md"
        if not skill_md.exists():
            continue
        fm, body = _parse_frontmatter(skill_md)
        name = _require_str(fm.get("name"), "name", skill_md, source)
        description = _require_str(fm.get("description"), "description", skill_md, source)
        if name != folder.name:
            raise CatalogError(
                f"{skill_md} (source `{source.name}`): "
                f"`name` ({name!r}) does not match folder ({folder.name!r})"
            )
        out.append(
            Artifact(
                kind="skill",
                source=source,
                name=name,
                description=description,
                distribution=None,
                tags=_tags(fm.get("tags"), skill_md, source),
                body=body,
                rel_source_path=str(skill_md.relative_to(source.local)),
            )
        )
    return out


def _collect_agents(source: Source) -> list[Artifact]:
    base = source.local / source.agents_path
    if not base.exists():
        return []
    out: list[Artifact] = []
    for agent_md in sorted(base.glob("*.md")):
        fm, body = _parse_frontmatter(agent_md)
        name = _require_str(fm.get("name"), "name", agent_md, source)
        description = _require_str(fm.get("description"), "description", agent_md, source)
        distribution = _require_str(
            fm.get("distribution"), "distribution", agent_md, source
        )
        if agent_md.stem != name:
            raise CatalogError(
                f"{agent_md} (source `{source.name}`): "
                f"`name` ({name!r}) does not match filename stem ({agent_md.stem!r})"
            )
        out.append(
            Artifact(
                kind="agent",
                source=source,
                name=name,
                description=description,
                distribution=distribution,
                tags=_tags(fm.get("tags"), agent_md, source),
                body=body,
                rel_source_path=str(agent_md.relative_to(source.local)),
            )
        )
    return out


def _source_link(artifact: Artifact) -> str:
    return (
        f"{artifact.source.repo_url}/blob/{artifact.source.branch}/"
        f"{artifact.rel_source_path}"
    )


def _render_artifact_page(artifact: Artifact) -> str:
    lines = [
        f"# {artifact.name}",
        "",
        f"> {artifact.description}",
        "",
        f"- **Source plugin:** `{artifact.source.name}`",
    ]
    if artifact.distribution:
        lines.append(f"- **Distribution:** `{artifact.distribution}`")
    if artifact.tags:
        lines.append("- **Tags:** " + " ".join(f"`{t}`" for t in artifact.tags))
    lines.extend(
        [
            f"- **Source file:** [{artifact.rel_source_path}]({_source_link(artifact)})",
            "",
            "---",
            "",
            artifact.body.rstrip(),
            "",
        ]
    )
    return "\n".join(lines)


def _render_section_index(kind: str, artifacts: list[Artifact]) -> str:
    title = "Skills" if kind == "skill" else "Agents"
    lines = [f"# {title}", ""]
    by_source: dict[str, list[Artifact]] = defaultdict(list)
    for artifact in artifacts:
        by_source[artifact.source.name].append(artifact)
    for source_name in sorted(by_source):
        lines.append(f"## {source_name}")
        lines.append("")
        lines.append("| Name | Description |")
        lines.append("|---|---|")
        for artifact in sorted(by_source[source_name], key=lambda a: a.name):
            desc = artifact.description.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| [`{artifact.name}`]({source_name}/{artifact.name}.md) | {desc} |"
            )
        lines.append("")
    return "\n".join(lines)


def _render_summary(kind: str, artifacts: list[Artifact]) -> str:
    title = "Skills" if kind == "skill" else "Agents"
    lines = [f"# {title}", "", "- [Overview](index.md)"]
    by_source: dict[str, list[Artifact]] = defaultdict(list)
    for artifact in artifacts:
        by_source[artifact.source.name].append(artifact)
    for source_name in sorted(by_source):
        lines.append(f"- {source_name}:")
        for artifact in sorted(by_source[source_name], key=lambda a: a.name):
            lines.append(
                f"    - [{artifact.name}]({source_name}/{artifact.name}.md)"
            )
    return "\n".join(lines)


def _render_tag_index(all_artifacts: list[Artifact]) -> str:
    by_tag: dict[str, list[Artifact]] = defaultdict(list)
    for artifact in all_artifacts:
        for tag in artifact.tags:
            by_tag[tag].append(artifact)
    lines = ["# Tags", ""]
    if not by_tag:
        lines.append("*No artifacts declare tags yet.*")
        lines.append("")
        return "\n".join(lines)
    for tag in sorted(by_tag):
        lines.append(f"## `{tag}`")
        lines.append("")
        for artifact in sorted(
            by_tag[tag], key=lambda a: (a.kind, a.source.name, a.name)
        ):
            page = f"{artifact.kind}s/{artifact.source.name}/{artifact.name}.md"
            lines.append(
                f"- [{artifact.kind}: {artifact.name}]({page}) — {artifact.source.name}"
            )
        lines.append("")
    return "\n".join(lines)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        sources = _load_sources(repo_root)
        skills: list[Artifact] = []
        agents: list[Artifact] = []
        for source in sources:
            skills.extend(_collect_skills(source))
            agents.extend(_collect_agents(source))
    except CatalogError as exc:
        print(f"[gen_catalog] error: {exc}", file=sys.stderr)
        return 2

    skills_index = _render_section_index("skill", skills) if skills else ""
    agents_index = _render_section_index("agent", agents) if agents else ""
    skills_summary = _render_summary("skill", skills) if skills else ""
    agents_summary = _render_summary("agent", agents) if agents else ""
    tag_index = _render_tag_index(skills + agents)

    docs = repo_root / DOCS_DIR
    for locale in LOCALES:
        locale_root = docs / locale
        for artifact in skills + agents:
            out = (
                locale_root
                / f"{artifact.kind}s"
                / artifact.source.name
                / f"{artifact.name}.md"
            )
            _write(out, _render_artifact_page(artifact))
        if skills:
            _write(locale_root / "skills" / "index.md", skills_index)
            _write(locale_root / "skills" / "SUMMARY.md", skills_summary)
        if agents:
            _write(locale_root / "agents" / "index.md", agents_index)
            _write(locale_root / "agents" / "SUMMARY.md", agents_summary)
        _write(locale_root / TAG_INDEX_PATH, tag_index)

    print(
        f"[gen_catalog] wrote {len(skills)} skills, {len(agents)} agents, tag index "
        f"for locales {', '.join(LOCALES)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
