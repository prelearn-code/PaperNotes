import copy
import random
import unittest
from prototype import Client, EpochCatalog, Merkle, ctx, respond, verify_row


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        cls.snap = cls.client.build([('f0',['alpha'],b'A'*64), ('f1',['beta'],b'B'*64)],
                                   rows=4, blocks=16, block_bytes=32)
        cls.entries = cls.client.open_manifest(cls.snap.pin, cls.snap.manifest)

    def round(self, c=5):
        ch = self.client.challenge(self.snap.pin, self.entries, c, random.Random(21))
        return ch, respond(self.snap, ch)

    def test_honest_and_exact_local_results(self):
        ch, resp = self.round()
        self.assertTrue(self.client.verify(self.snap.pin,self.entries,ch,resp))
        self.assertEqual(self.client.local_results(self.entries,'alpha'),['f0'])
        self.assertEqual(self.client.local_results(self.entries,'absent'),[])

    def test_all_sample_counts(self):
        for c in range(1,17):
            ch,resp=self.round(c)
            self.assertTrue(self.client.verify(self.snap.pin,self.entries,ch,resp))
            if c==16:
                self.assertTrue(all(not proof for _,proof in resp.values()))

    def test_manifest_tampering(self):
        value=bytearray(self.snap.manifest); value[-1]^=1
        with self.assertRaises(ValueError):
            self.client.open_manifest(self.snap.pin,bytes(value))

    def test_sample_tampering(self):
        ch,resp=self.round(); a=next(iter(resp)); i=ch[a][0]
        v=bytearray(resp[a][0][i]); v[-1]^=1; resp[a][0][i]=bytes(v)
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,resp))

    def test_missing_dummy_rejected(self):
        ch,resp=self.round()
        a=next(e['alias'] for e in self.entries if e['fid'] is None)
        del resp[a]
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,resp))

    def test_proof_tampering_and_extras(self):
        ch,resp=self.round(); a=next(iter(resp)); node=next(iter(resp[a][1]))
        resp[a][1][node]=b'0'*32
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,resp))
        ch,resp=self.round(); resp[a][1][(99,0)]=b'0'*32
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,resp))

    def test_cross_row_and_position_substitution(self):
        ch,resp=self.round(); a,b=list(resp)[:2]
        resp[a]=resp[b]
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,resp))
        ch,resp=self.round(); i,j=ch[a][:2]
        resp[a][0][i],resp[a][0][j]=resp[a][0][j],resp[a][0][i]
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,resp))

    def test_old_epoch_cannot_be_relabelled_current(self):
        new=self.client.build([('f0',['alpha'],b'C'*64)],rows=4,blocks=16,block_bytes=32,epoch=2)
        with self.assertRaises(ValueError):
            self.client.open_manifest(new.pin,self.snap.manifest)
        # An explicitly pinned old query remains valid; no silent promotion.
        ch,resp=self.round()
        self.assertTrue(self.client.verify(self.snap.pin,self.entries,ch,resp))

    def test_replay_distinct_challenge(self):
        ch,resp=self.round()
        new_ch=self.client.challenge(self.snap.pin,self.entries,5,random.Random(22))
        self.assertFalse(self.client.verify(self.snap.pin,self.entries,new_ch,resp))

    def test_invalid_sample_parameters(self):
        for c in [0,17]:
            with self.assertRaises(ValueError):
                self.client.challenge(self.snap.pin,self.entries,c)

    def test_exhaustive_merkle_subsets(self):
        values=[bytes([i])*8 for i in range(8)]
        context=b'unit-context'; tree=Merkle(context,values)
        for mask in range(1,256):
            indices=[i for i in range(8) if mask>>i&1]
            self.assertTrue(verify_row(context,8,indices,{i:values[i] for i in indices},tree.proof(indices),tree.root))

    def test_all_row_omission_patterns_keyword_independence(self):
        ch,resp=self.round()
        aliases=list(resp)
        for mask in range(16):
            modified={a:v for i,(a,v) in enumerate(resp.items()) if not mask>>i&1}
            # The wire verifier intentionally has no keyword argument.
            alpha=self.client.verify(self.snap.pin,self.entries,ch,modified)
            beta=self.client.verify(self.snap.pin,self.entries,ch,modified)
            self.assertEqual(alpha,beta)
            self.assertEqual(alpha,mask==0)

    def test_challenge_does_not_use_true_target(self):
        ch1=self.client.challenge(self.snap.pin,self.entries,5,random.Random(12))
        alternate=copy.deepcopy(self.entries)
        for e in alternate:
            e['words']=['totally-different']
        ch2=self.client.challenge(self.snap.pin,alternate,5,random.Random(12))
        self.assertEqual(ch1,ch2)

    def test_malformed_response_rejected(self):
        ch,resp=self.round(); a=next(iter(resp))
        for bad in [None, 7, (None,None), ({},), ([], {})]:
            altered=copy.deepcopy(resp); altered[a]=bad
            self.assertFalse(self.client.verify(self.snap.pin,self.entries,ch,altered))

    def test_epoch_commit_pin_and_expiry(self):
        catalog=EpochCatalog(self.snap.pin,max_lease=4)
        sid=catalog.open()
        new=self.client.build([('f2',['gamma'],b'C'*64)],rows=4,blocks=16,block_bytes=32,epoch=2)
        catalog.commit(new.pin)
        self.assertEqual(catalog.pinned(sid),self.snap.pin)
        self.assertEqual(catalog.pinned(catalog.open()),new.pin)
        with self.assertRaises(ValueError):
            catalog.commit(self.snap.pin)
        catalog.advance(4)
        with self.assertRaises(ValueError):
            catalog.pinned(sid)

    def test_deletion_rebuild_changes_authenticated_result(self):
        new=self.client.build([('f1',['beta'],b'B'*64)],rows=4,blocks=16,block_bytes=32,epoch=2)
        entries=self.client.open_manifest(new.pin,new.manifest)
        self.assertEqual(self.client.local_results(entries,'alpha'),[])
        self.assertEqual(self.client.local_results(self.entries,'alpha'),['f0'])


if __name__=='__main__':
    unittest.main(verbosity=2)
