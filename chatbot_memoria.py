#!/usr/bin/env python3
"""Motor de memória para chat baseado somente no conteúdo enviado pelo usuário."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

MEMORY_FILE = Path("memoria_usuario.json")
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "é", "em",
    "para", "por", "com", "que", "na", "no", "nas", "nos", "se", "ao", "à", "às", "ou",
    "como", "sobre", "me", "te", "lhe", "eu", "você", "voce", "ele", "ela", "nós", "nosso",
    "minha", "meu", "sua", "seu", "isso", "isto", "aquilo", "foi", "ser", "estar", "está",
}


@dataclass
class KnowledgeEntry:
    text: str
    created_at: str
    source: str = "chat"


class MemoryChatbot:
    def __init__(self, memory_path: Path = MEMORY_FILE) -> None:
        self.memory_path = memory_path
        self.knowledge: List[KnowledgeEntry] = []
        self._load_memory()

    def _load_memory(self) -> None:
        if not self.memory_path.exists():
            return

        try:
            raw = json.loads(self.memory_path.read_text(encoding="utf-8"))
            self.knowledge = [
                KnowledgeEntry(
                    text=item.get("text", ""),
                    created_at=item.get("created_at", datetime.now(timezone.utc).isoformat()),
                    source=item.get("source", "chat"),
                )
                for item in raw
                if item.get("text")
            ]
        except (json.JSONDecodeError, OSError, TypeError):
            self.knowledge = []

    def _save_memory(self) -> None:
        payload = [asdict(item) for item in self.knowledge]
        self.memory_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
        return {w for w in words if w not in STOPWORDS and len(w) > 1}

    def _find_relevant_memories(self, prompt: str, limit: int = 5) -> List[KnowledgeEntry]:
        prompt_tokens = self._tokenize(prompt)
        if not prompt_tokens:
            return []

        scored = []
        for item in self.knowledge:
            item_tokens = self._tokenize(item.text)
            overlap = len(prompt_tokens & item_tokens)
            if overlap > 0:
                scored.append((overlap, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def learn(self, user_message: str, source: str = "chat") -> None:
        cleaned = user_message.strip()
        if not cleaned:
            return

        self.knowledge.append(
            KnowledgeEntry(
                text=cleaned,
                created_at=datetime.now(timezone.utc).isoformat(),
                source=source,
            )
        )
        self._save_memory()

    def learn_from_text_block(self, content: str, source: str) -> int:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            self.learn(line, source=source)
        return len(lines)

    def respond(self, user_message: str) -> str:
        relevant = self._find_relevant_memories(user_message)

        if not self.knowledge:
            return (
                "Ainda não tenho conhecimento salvo. "
                "Me ensine algo ou envie um arquivo para eu aprender."
            )

        if not relevant:
            return (
                "Eu só posso responder com base no que você já me ensinou. "
                "Ainda não encontrei algo relacionado a isso na minha memória."
            )

        bullets = "\n".join(f"- ({entry.source}) {entry.text}" for entry in relevant)
        return (
            "Com base no que você me ensinou, encontrei estas informações relacionadas:\n"
            f"{bullets}"
        )

    def clear(self) -> None:
        self.knowledge = []
        self._save_memory()

    def stats(self) -> dict:
        return {"total": len(self.knowledge)}
