import hashlib
import math
import re

EMBEDDING_DIMENSION = 384
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class LocalHashEmbeddings:
    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSION
        for token in TOKEN_PATTERN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % EMBEDDING_DIMENSION
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)


_embedding_function: LocalHashEmbeddings | None = None


def get_embedding_function() -> LocalHashEmbeddings:
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = LocalHashEmbeddings()
    return _embedding_function