"""Reads YAML knowledge files and indexes them into the vector database."""

from pathlib import Path

import structlog
import yaml

from app.embedding import EmbeddingEngine
from app.vectordb.repository import LANG_TO_TSCONFIG, VectorChunkRepository

logger = structlog.get_logger(__name__)

SOURCE_TYPE = "care_rule"


class KnowledgeIngestor:
    """Reads YAML knowledge files and indexes them into the vector database."""

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        chunk_repo: VectorChunkRepository,
        knowledge_path: str = "/app/knowledge",
    ) -> None:
        self._embedding = embedding_engine
        self._repo = chunk_repo
        self._knowledge_path = Path(knowledge_path)

    def ingest_all(self) -> dict:
        """Index all YAML files under the knowledge path. Returns summary dict."""
        if not self._knowledge_path.exists():
            logger.warning("knowledge_path_not_found", path=str(self._knowledge_path))
            return {"status": "skipped", "reason": "knowledge_path_not_found"}

        yaml_files = sorted(self._knowledge_path.rglob("*.yaml"))
        if not yaml_files:
            logger.warning("knowledge_no_yaml_files", path=str(self._knowledge_path))
            return {"status": "skipped", "reason": "no_yaml_files"}

        total_chunks = 0
        total_files = 0

        for yaml_file in yaml_files:
            count = self._ingest_file(yaml_file)
            total_chunks += count
            total_files += 1

        logger.info("knowledge_ingest_complete", files=total_files, chunks=total_chunks)
        return {"status": "ok", "files": total_files, "chunks": total_chunks}

    def _ingest_file(self, yaml_file: Path) -> int:
        """Parse a single YAML file and upsert its chunks. Returns chunk count."""
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "chunks" not in data:
            logger.warning("knowledge_file_no_chunks", file=str(yaml_file))
            return 0

        category = data.get("category", yaml_file.parent.name)
        language = data.get("language", "de")
        ts_config = LANG_TO_TSCONFIG.get(language, "simple")
        file_stem = yaml_file.stem
        file_metadata = {
            "category": category,
            "tags": data.get("tags", []),
            "expertise_level": data.get("expertise_level", []),
            "applicable_phases": data.get("applicable_phases", []),
        }

        chunks_data = []
        texts = []
        for chunk in data["chunks"]:
            chunk_id = chunk.get("id", "")
            title = chunk.get("title", "")
            content = chunk.get("content", "")
            text = f"{title}\n\n{content}".strip()
            if not text:
                continue

            source_key = f"{category}/{file_stem}#{chunk_id}"
            chunk_metadata = {**file_metadata, **(chunk.get("metadata") or {})}

            meta_parts = []
            for key in (
                "nutrient",
                "symbol",
                "deficiency_type",
                "affected_leaves",
                "severity_indicator",
                "type",
                "trigger",
                "approach",
            ):
                val = chunk_metadata.get(key)
                if val:
                    meta_parts.append(f"{key}: {val}")
            embed_text = text
            if meta_parts:
                embed_text = f"{text}\n\n{' | '.join(meta_parts)}"

            chunks_data.append(
                {
                    "source_key": source_key,
                    "source_type": SOURCE_TYPE,
                    "title": title,
                    "content": content,
                    "metadata": chunk_metadata,
                    "language": language,
                    "ts_config": ts_config,
                }
            )
            texts.append(embed_text)

        if not texts:
            return 0

        embeddings = self._embedding.embed_batch(texts, prefix="passage: ")

        for chunk_dict, embedding in zip(chunks_data, embeddings, strict=True):
            chunk_dict["embedding"] = embedding

        count = self._repo.upsert_batch(chunks_data)

        logger.info("knowledge_file_ingested", file=f"{category}/{file_stem}", chunks=count)
        return count
