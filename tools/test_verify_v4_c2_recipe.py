"""Host-only behavioral controls for the frozen C2 production contract."""
import json
from pathlib import Path
import tempfile
import unittest

if __package__:
    from . import cad_verify_v4_c2_recipe as registry
else:
    import cad_verify_v4_c2_recipe as registry


class ProductionRecipeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for relative in (registry.RECIPE_PATH, registry.REGISTRATION_PATH):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((registry.ROOT / relative).read_bytes())

    def rewrite(self, relative, update):
        path = self.root / relative
        value = json.loads(path.read_bytes())
        update(value)
        path.write_text(json.dumps(value), encoding='utf-8')

    def test_mutating_loaded_recipe_cannot_change_authorized_policy(self):
        first = registry.load(self.root)
        first['recipe']['foreground']['channel'] = 'red'
        second = registry.load(self.root)
        self.assertEqual(second['recipe']['foreground']['channel'], 'alpha')

    def test_scale_modes_cannot_be_combined_or_rounded_after_fitting(self):
        recipe = registry.load(self.root)['recipe']
        recipe['scale']['mm_per_pixel'] = .5
        with self.assertRaises(ValueError):
            registry.plans.validate_document(recipe, 'contour-recipe', profile='c-s1')
        with self.assertRaises(ValueError):
            registry.contours.validate_recipe(recipe)
        del recipe['scale']['mm_per_pixel']
        recipe['rounding'] = dict(allowed=True, radius_mm=.25)
        with self.assertRaisesRegex(ValueError, 'cannot_simplify_or_round'):
            registry.contours.validate_recipe(recipe)

    def test_equivalent_json_byte_change_is_not_accepted(self):
        path = self.root / registry.RECIPE_PATH
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'c2_production_file_sha256'):
            registry.load(self.root)


    def test_registration_cannot_redirect_recipe(self):
        self.rewrite(registry.REGISTRATION_PATH,
                     lambda r: r['entries'][0]['recipe'].update(path='../other.json'))
        with self.assertRaisesRegex(ValueError, 'c2_production_file_sha256'):
            registry.bindings(self.root)

    def test_missing_either_registered_file_fails_closed(self):
        for relative in (registry.RECIPE_PATH, registry.REGISTRATION_PATH):
            with self.subTest(path=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaisesRegex(ValueError, 'input_path_missing'):
                        registry.load(self.root)
                finally:
                    path.write_bytes(original)

    def test_private_root_is_rejected_before_filesystem_access(self):
        with self.assertRaisesRegex(ValueError, 'private_input_path_forbidden'):
            registry.load(self.root / 'pilot-user')


if __name__ == '__main__':
    unittest.main()
