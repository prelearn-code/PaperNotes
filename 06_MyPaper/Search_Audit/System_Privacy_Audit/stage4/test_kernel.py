import copy
import unittest
from kernel import *


class KernelTests(unittest.TestCase):
    def setUp(self):
        self.o = Owner(512)
        self.c = Cache(self.o.pin(), [t.values for t in self.o.index], self.o.n)

    def audit(self, q=64):
        ch, _ = challenge(self.o, self.c, q)
        return ch, respond(self.o.data, self.o.tags, ch)

    def test_honest_and_exact_result(self):
        expected = [i for i in range(512) if all(m[i] for m in self.o.maps)]
        self.assertEqual(self.c.result(), expected)
        ch, r = self.audit()
        self.assertTrue(verify(self.o, ch, r, self.o.pin()))
        self.assertTrue(all(i in expected for i, j, a in ch.items))

    def test_changed_ciphertext_rejected(self):
        ch, _ = self.audit()
        i, j, a = ch.items[0]
        d = dict(self.o.data)
        x = d[i, j]
        d[i, j] = bytes([x[0]^1])+x[1:]
        self.assertFalse(verify(self.o, ch, respond(d, self.o.tags, ch), self.o.pin()))

    def test_missing_block_cannot_respond(self):
        ch, _ = self.audit()
        d = dict(self.o.data)
        del d[ch.items[0][:2]]
        with self.assertRaises(KeyError):
            respond(d, self.o.tags, ch)

    def test_substitution_rejected(self):
        ch, _ = self.audit()
        bad = copy.deepcopy(ch)
        i, j, a = bad.items[0]
        bad.items[0] = ((i+1)%512, j, a)
        self.assertFalse(verify(self.o, ch, respond(self.o.data, self.o.tags, bad), self.o.pin()))

    def test_replay_even_with_fresh_nonce_rejected(self):
        ch, old = self.audit()
        newer, _ = self.audit()
        forged = (newer.nonce, old[1], old[2])
        self.assertFalse(verify(self.o, newer, forged, self.o.pin()))

    def test_omitted_delta_transactional_rejection(self):
        old = self.c.pin
        delta = self.o.keyword(0, 0, not self.o.maps[0][0])
        with self.assertRaises(ValueError):
            self.c.patch(self.o.pin(), {})
        self.assertEqual(self.c.pin, old)
        self.c.patch(self.o.pin(), delta)

    def test_incorrect_delta_transactional_rejection(self):
        old_roots = tuple(t.root for t in self.c.trees)
        self.o.keyword(0, 0, not self.o.maps[0][0])
        with self.assertRaises(ValueError):
            self.c.patch(self.o.pin(), {0: {0: bytes(64)}})
        self.assertEqual(tuple(t.root for t in self.c.trees), old_roots)

    def test_metadata_proof_tamper(self):
        vals, proof = self.o.meta.open([0, 3, 200])
        vals[0] = bytes(48)
        self.assertFalse(verify_open(self.o.meta.root, 512, vals, proof))

    def test_content_update_only_one_tag_and_no_index_change(self):
        ch, old_response = self.audit()
        old_tags = self.o.tags.copy()
        old_roots = self.o.pin().roots
        i, j, _ = ch.items[0]
        self.o.content(i, j, bytes([7])*PLAINTEXT)
        self.assertEqual(old_roots, self.o.pin().roots)
        self.assertEqual(sum(v != self.o.tags[k] for k, v in old_tags.items()), 1)
        self.assertFalse(verify(self.o, ch, old_response, self.o.pin()))
        self.c.patch(self.o.pin(), {})
        ch, r = self.audit()
        self.assertTrue(verify(self.o, ch, r, self.o.pin()))

    def test_old_data_and_tag_under_new_version_rejected(self):
        i = self.c.result()[0]
        old_data, old_tags = self.o.data.copy(), self.o.tags.copy()
        self.o.content(i, 0, bytes([9])*PLAINTEXT)
        self.c.patch(self.o.pin(), {})
        ch = Challenge(self.o.pin(), secrets.token_bytes(32), [(i, 0, 17)], [self.o.label(i, 0)])
        self.assertFalse(verify(self.o, ch, respond(old_data, old_tags, ch), self.o.pin()))

    def test_delete_reinsert_generation_and_keyword_no_retag(self):
        i = self.c.result()[0]
        old_label = self.o.label(i, 0)
        delta = self.o.alive(i, False)
        self.c.patch(self.o.pin(), delta)
        self.assertNotIn(i, self.c.result())
        delta = self.o.alive(i, True)
        self.c.patch(self.o.pin(), delta)
        self.assertIn(i, self.c.result())
        self.assertNotEqual(old_label, self.o.label(i, 0))
        tags = self.o.tags.copy()
        self.o.keyword(i, 0, False)
        self.assertEqual(tags, self.o.tags)

    def test_empty_is_search_certificate_not_possession(self):
        o = Owner(512, density=0)
        c = Cache(o.pin(), [t.values for t in o.index], o.n)
        self.assertEqual(challenge(o, c, 64), (None, 0))

    def test_random_updates_match_full_recomputation(self):
        rng = random.Random(91)
        for _ in range(60):
            i, k = rng.randrange(512), rng.randrange(2)
            delta = self.o.keyword(i, k, not self.o.maps[k][i])
            self.c.patch(self.o.pin(), delta)
            self.assertEqual(self.c.result(), [i for i in range(512) if all(m[i] for m in self.o.maps)])

    def test_no_server_claimed_result_or_owner_index_used(self):
        expected = self.c.result()
        self.o.maps = None
        ch, r = self.audit()
        self.assertTrue(all(i in expected for i, j, a in ch.items))
        self.assertTrue(verify(self.o, ch, r, self.o.pin()))

    def test_omission_of_one_of_two_changed_pages(self):
        o = Owner(1024)
        c = Cache(o.pin(), [t.values for t in o.index], o.n)
        d1 = o.keyword(1, 0, not o.maps[0][1])
        d2 = o.keyword(513, 0, not o.maps[0][513])
        with self.assertRaises(ValueError):
            c.patch(o.pin(), d1)
        c.patch(o.pin(), {0: {**d1[0], **d2[0]}})
        self.assertEqual(c.result(), [i for i in range(1024) if all(m[i] for m in o.maps)])

    def test_rollback_rejected(self):
        old = self.c.pin
        d = self.o.keyword(0, 0, not self.o.maps[0][0])
        self.c.patch(self.o.pin(), d)
        with self.assertRaises(ValueError):
            self.c.patch(old, {})

    def test_noncanonical_aggregate_rejected(self):
        ch, r = self.audit()
        bad = (r[0], r[1], r[2]+P)
        self.assertFalse(verify(self.o, ch, bad, self.o.pin()))

    def test_zero_sample_audit_rejected(self):
        with self.assertRaises(ValueError):
            challenge(self.o, self.c, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
