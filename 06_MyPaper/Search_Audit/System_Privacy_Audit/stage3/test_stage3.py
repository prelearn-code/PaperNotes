import random
import unittest
from auth_oram import PathORAM, reconstruct
from mechanism import Audit, pack, logical_cost


class ORAMTests(unittest.TestCase):
    def test_random_reads_writes_and_root(self):
        expected = {i:pack(i) for i in range(32)}
        o = PathORAM(expected,32)
        rng = random.Random(23)
        for _ in range(150):
            i = rng.randrange(32)
            if rng.randrange(3)==0:
                new = pack(rng.randrange(10**8))
                self.assertEqual(o.access(i,new),expected[i])
                expected[i]=new
            else:
                self.assertEqual(o.access(i),expected[i])
            self.assertEqual(o.root,o.store.levels[-1][0])

    def test_ciphertext_tamper_failstop(self):
        o=PathORAM({0:pack(1)},16)
        raw=o.store.buckets[0]
        o.store.buckets[0]=bytes([raw[0]^1])+raw[1:]
        with self.assertRaises(ValueError): o.access(0)
        with self.assertRaisesRegex(ValueError,'fail-stop'): o.access(1)

    def test_replay_bucket(self):
        o=PathORAM({},16)
        old=o.store.buckets[0]
        o.access(0,pack(99))
        o.store.buckets[0]=old
        with self.assertRaises(ValueError): o.access(0)

    def test_missing_proof(self):
        o=PathORAM({},16)
        values,proof=o.store.get(o.path(o.position[0]))
        proof.pop(next(iter(proof)))
        with self.assertRaises(ValueError): reconstruct(values,proof,o.store.size)


class MechanismTests(unittest.TestCase):
    def build(self,method,count=5):
        return Audit(method,8,8,2,3,count)

    def test_all_methods_same_samples(self):
        answers=[]
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method)
            a.oram.reset_metrics()
            out,meta=a.query(0,19,random.Random(51))
            self.assertEqual((meta,a.oram.accesses),logical_cost(method,8,19))
            answers.append([(fid,j) for fid,j,_ in out])
        self.assertEqual(answers[0],answers[1])
        self.assertEqual(answers[0],answers[2])

    def test_empty_same_schedule(self):
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method,0)
            a.oram.reset_metrics()
            result,_=a.query(0,5,random.Random(5))
            self.assertEqual(result,[])
            self.assertEqual(a.oram.accesses,logical_cost(method,8,5)[1])

    def test_duplicates_do_not_shorten(self):
        for method in ('rank_serial','rank_batch','dense'):
            for count in (1,7):
                a=self.build(method,count)
                a.oram.reset_metrics()
                a.query(0,5,random.Random(2))
                self.assertEqual(a.oram.accesses,logical_cost(method,8,5)[1])

    def test_delete_and_insert_preserve_domain(self):
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method)
            a.remove(0,1)
            result,_=a.query(0,50,random.Random(3))
            self.assertEqual({fid for fid,j,v in result},{0,2,3,4})
            a.insert(0,6)
            result,_=a.query(0,50,random.Random(3))
            self.assertEqual({fid for fid,j,v in result},{0,2,3,4,6})

    def test_remove_last_and_single(self):
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method,1)
            a.remove(0,0)
            self.assertEqual(a.query(0,3)[0],[])
            a.insert(0,7)
            self.assertEqual({x[0] for x in a.query(0,3)[0]},{7})

    def test_modify_version(self):
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method,1)
            a.modify(0)
            out,_=a.query(0,3)
            self.assertTrue(all(int.from_bytes(raw[16:24],'big')==2 for fid,j,raw in out))

    def test_query_does_not_use_owner_membership(self):
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method)
            del a.owner_lists
            self.assertEqual(len(a.query(0,3)[0]),3)

    def test_dense_dominates_batch_public_counts(self):
        for h in range(1,13):
            for q in (1,2,3,16,64,256,919):
                r=2**h
                self.assertLessEqual(logical_cost('dense',r,q)[1],logical_cost('rank_batch',r,q)[1])

    def test_random_updates_exhaustive_rank_mapping(self):
        class Ranks:
            def __init__(self,n): self.values=list(range(n))
            def randrange(self,n): return self.values.pop(0) if self.values else 0
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method)
            members=list(range(5))
            rng=random.Random(84)
            for _ in range(18):
                if members and (len(members)==8 or rng.randrange(2)):
                    pos=rng.randrange(len(members));fid=members[pos]
                    a.remove(0,fid)
                    members[pos]=members[-1];members.pop()
                else:
                    fid=rng.choice([i for i in range(8) if i not in members])
                    a.insert(0,fid);members.append(fid)
                out,_=a.query(0,max(1,len(members)),Ranks(len(members)))
                self.assertEqual([fid for fid,j,raw in out],members)

    def test_keyword_domains_are_independent(self):
        for method in ('rank_serial','rank_batch','dense'):
            a=self.build(method,1)
            a.remove(0,0)
            self.assertEqual(a.query(0,3)[0],[])
            self.assertEqual({fid for fid,j,raw in a.query(1,3)[0]},{0})


if __name__=='__main__': unittest.main(verbosity=2)
