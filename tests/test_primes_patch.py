"""Fail-closed profile checks and scoped editing for optional Primes dispatch."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'patches/build-scripts/apply-primes-privacy.py'
spec = importlib.util.spec_from_file_location('primes_patch', path)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class PrimesPatch(unittest.TestCase):
    def test_only_dispatch_body_changes(self):
        prefix = '.class public final Lcse;\n.method public a()V\n    return-void\n.end method\n'
        suffix = '\n.method public c()V\n    return-void\n.end method\n'
        original = prefix + patch.METHOD + '\n    .locals 2\n    return-object p1\n.end method' + suffix
        result = patch.replace_dispatch(original)
        self.assertTrue(result.startswith(prefix + patch.METHOD + '\n'))
        self.assertTrue(result.endswith('.end method' + suffix))
        self.assertEqual(result.count('.end method'), original.count('.end method'))
        self.assertNotIn('return-object p1', result)
        self.assertNotIn('invoke-', result, 'discard path cannot call network or dispatch APIs')
        self.assertIn('Lgdb;->a:Lcom/google/common/util/concurrent/ListenableFuture;', result)
        self.assertIn('return-object v0', result)

    def test_missing_or_duplicate_dispatch_rejected(self):
        with self.assertRaises(ValueError):
            patch.replace_dispatch('.class public final Lcse;\n')
        method = patch.METHOD + '\n    return-object p1\n.end method\n'
        with self.assertRaises(ValueError):
            patch.replace_dispatch(method + method)

    def test_changed_profiles_rejected(self):
        for expected in [patch.CSE_HASH, patch.GDB_HASH]:
            with self.assertRaises(ValueError):
                patch.require_profile('unsupported source', expected)

    def test_exact_profile_digest_required(self):
        text = 'known fixture\n'
        digest = hashlib.sha256(text.encode()).hexdigest()
        patch.require_profile(text, digest)
        with self.assertRaises(ValueError):
            patch.require_profile(text + '# changed\n', digest)


if __name__ == '__main__':
    unittest.main()
