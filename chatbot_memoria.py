#!/usr/bin/env python3
"""Motor de memória para chat baseado somente no conteúdo enviado pelo usuário."""

from __future__ import annotations

import json
import re
from collections import Counter, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, List

MEMORY_FILE = Path("memoria_usuario.json")
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "é", "em",
    "para", "por", "com", "que", "na", "no", "nas", "nos", "se", "ao", "à", "às", "ou",
    "como", "sobre", "me", "te", "lhe", "eu", "você", "voce", "ele", "ela", "nós", "nosso",
    "minha", "meu", "sua", "seu", "isso", "isto", "aquilo", "foi", "ser", "estar", "está",
}

POSITIVE_WORDS = {
    "bom", "boa", "ótimo", "otimo", "excelente", "feliz", "gostei", "amo", "legal", "incrível",
    "incrivel", "perfeito", "melhor", "maravilhoso", "positivo", "curti", "sucesso", "show",
}

NEGATIVE_WORDS = {
    "ruim", "péssimo", "pessimo", "horrível", "horrivel", "triste", "odeio", "chato", "pior",
    "problema", "erro", "falha", "negativo", "raiva", "cansado", "medo", "ansioso", "difícil", "dificil",
}


@dataclass
class KnowledgeEntry:
    text: str
    created_at: str
    source: str = "chat"
    score: int = 0


class MemoryChatbot:
    def __init__(self, memory_path: Path = MEMORY_FILE) -> None:
        self.memory_path = memory_path
        self.knowledge: List[KnowledgeEntry] = []
        self.recent_user_turns: Deque[str] = deque(maxlen=5)
        self.recent_bot_turns: Deque[str] = deque(maxlen=5)
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
                    score=int(item.get("score", 0)),
                )
                for item in raw
                if item.get("text")
            ]
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
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

    @staticmethod
    def _sentiment_score(text: str) -> int:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
        positive_hits = sum(1 for token in tokens if token in POSITIVE_WORDS)
        negative_hits = sum(1 for token in tokens if token in NEGATIVE_WORDS)

        if positive_hits == 0 and negative_hits == 0:
            return 0

        raw_score = positive_hits - negative_hits
        if raw_score > 0:
            return min(5, raw_score)
        return max(-5, raw_score)

    def _find_relevant_memories(self, prompt: str, limit: int = 5) -> List[KnowledgeEntry]:
        prompt_tokens = self._tokenize(prompt)
        if not prompt_tokens:
            return []

        scored = []
        for item in self.knowledge:
            item_tokens = self._tokenize(item.text)
            overlap = len(prompt_tokens & item_tokens)
            if overlap > 0:
                scored.append((overlap, item.score, item))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [entry for _, _, entry in scored[:limit]]

    def detect_patterns(self, prompt: str, top_n: int = 3) -> List[str]:
        prompt_tokens = self._tokenize(prompt)
        if not prompt_tokens:
            return []

        token_counter: Counter[str] = Counter()
        for item in self.knowledge:
            for token in self._tokenize(item.text):
                if token in prompt_tokens:
                    token_counter[token] += 1

        return [token for token, _ in token_counter.most_common(top_n)]

    def learn(self, user_message: str, source: str = "chat") -> int:
        cleaned = user_message.strip()
        if not cleaned:
            return 0

        score = self._sentiment_score(cleaned)
        self.knowledge.append(
            KnowledgeEntry(
                text=cleaned,
                created_at=datetime.now(timezone.utc).isoformat(),
                source=source,
                score=score,
            )
        )
        self._save_memory()
        return score

    def learn_from_text_block(self, content: str, source: str) -> int:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            self.learn(line, source=source)
        return len(lines)

    def respond(self, user_message: str) -> dict:
        user_score = self._sentiment_score(user_message)
        patterns = self.detect_patterns(user_message)
        relevant = self._find_relevant_memories(user_message)

        if not self.knowledge:
            text = (
                "Ainda não tenho conhecimento salvo. "
                "Me ensine algo ou envie um arquivo para eu aprender."
            )
        elif not relevant:
            text = (
                "Eu só posso responder com base no que você já me ensinou. "
                "Ainda não encontrei algo relacionado a isso na minha memória."
            )
        else:
            bullets = "\n".join(f"- ({entry.source}, score {entry.score}) {entry.text}" for entry in relevant)
            context = ""
            if self.recent_user_turns:
                context = f"\nContexto recente: {' | '.join(list(self.recent_user_turns)[-2:])}"

            pattern_info = ""
            if patterns:
                pattern_info = f"\nPadrões detectados: {', '.join(patterns)}"

            text = (
                "Com base no que você me ensinou, encontrei estas informações relacionadas:\n"
                f"{bullets}{pattern_info}{context}"
            )

        self.recent_user_turns.append(user_message)
        self.recent_bot_turns.append(text)

        return {
            "text": text,
            "score": user_score,
            "patterns": patterns,
        }

    def clear(self) -> None:
        self.knowledge = []
        self.recent_user_turns.clear()
        self.recent_bot_turns.clear()
        self._save_memory()

    def stats(self) -> dict:
        if not self.knowledge:
            return {"total": 0, "avg_score": 0}

        avg = sum(entry.score for entry in self.knowledge) / len(self.knowledge)
        return {"total": len(self.knowledge), "avg_score": round(avg, 2)}
