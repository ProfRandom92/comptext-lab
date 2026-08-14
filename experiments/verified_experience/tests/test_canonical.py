import unittest

from verified_experience.canonical import canonical_bytes, sha256_digest
from verified_experience.models import ExperienceCandidate


class CanonicalizationTests(unittest.TestCase):
    def test_canonical_bytes_ignore_mapping_insertion_order(self):
        left = {"b": 2, "a": 1}
        right = {"a": 1, "b": 2}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))
        self.assertEqual(sha256_digest(left), sha256_digest(right))

    def test_digest_changes_when_scalar_changes(self):
        self.assertNotEqual(sha256_digest({"a": 1}), sha256_digest({"a": 2}))

    def test_utf8_is_deterministic_and_not_ascii_escaped(self):
        payload = {"text": "Grüße 世界"}
        encoded = canonical_bytes(payload)
        self.assertIn("Grüße 世界".encode("utf-8"), encoded)
        self.assertEqual(encoded, canonical_bytes(payload))

    def test_candidate_digest_is_recomputed_from_authoritative_fields(self):
        candidate = ExperienceCandidate.create(
            candidate_id="cand-1",
            kind="fact",
            content={"package_manager": "cargo"},
            scope="repo:comptext-lab",
            evidence_refs=(),
            producer="agent:test",
            confidence=0.9,
            created_at="2026-08-14T12:00:00Z",
        )
        self.assertEqual(candidate.canonical_digest, sha256_digest(candidate.canonical_payload()))


if __name__ == "__main__":
    unittest.main()
