from pathlib import Path
import json
import sqlite3
import subprocess
import tempfile
import unittest

from linux_kb import ingest, ingest_full, load_snapshot
from linux_kb.source_tree import SourceTree, matches_scope


class SnapshotIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root/'repo'
        self.repo.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.PIPE,text=True).strip()

    def test_invalid_ref_is_never_silently_a_fixture(self):
        self.git('init'); self.git('config','user.name','fixture'); self.git('config','user.email','fixture@example.invalid')
        (self.repo/'f.c').write_text('int original(void) { return 0; }\n')
        self.git('add','f.c'); self.git('commit','-m','original')
        for mode in ('local','full'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                if mode=='local': ingest(self.repo,'missing',self.root/'out',['*.c'])
                else: ingest_full(self.repo,'missing',self.root/'out.db')

    def test_dirty_and_untracked_bytes_do_not_change_pinned_index(self):
        self.git('init'); self.git('config','user.name','fixture'); self.git('config','user.email','fixture@example.invalid')
        (self.repo/'f.c').write_text('int original(void) { return 0; }\n')
        self.git('add','f.c'); self.git('commit','-m','original')
        (self.repo/'f.c').write_text('int dirty(void) { return 0; }\n')
        (self.repo/'untracked.c').write_text('int untracked(void) { return 0; }\n')
        ingest(self.repo,'HEAD',self.root/'out',['*.c'])
        names={n['name'] for n in load_snapshot(self.root/'out')['nodes'] if n['kind']=='function'}
        self.assertEqual({'original'},names)
        ingest_full(self.repo,'HEAD',self.root/'out.db')
        with sqlite3.connect(self.root/'out.db') as c:
            self.assertEqual([('original',)],c.execute("select name from nodes where kind='function'").fetchall())

    def test_fixture_requires_opt_in_and_nonempty_supported_scope(self):
        (self.repo/'f.c').write_text('int original(void) { return 0; }\n')
        with self.assertRaises(ValueError): ingest(self.repo,'fixture',self.root/'out',['*.c'])
        with self.assertRaises(ValueError): ingest(self.repo,'fixture',self.root/'out',['*.nothing'],fixture=True)
        with self.assertRaises(ValueError): ingest_full(self.root,'fixture',self.root/'none.db')

    def test_scoped_type_ids_and_definition_coordinates(self):
        (self.repo/'a.c').write_text('// local mentioned here\nstruct local { int x; };\n')
        (self.repo/'b.c').write_text('struct local { int y; };\n')
        (self.repo/'cmd.h').write_text('// BPF_PROG_LOAD mentioned here\nenum bpf_cmd {\n BPF_PROG_LOAD,\n};\n')
        ingest(self.repo,'fixture',self.root/'out',['*.c','*.h'],fixture=True)
        nodes=load_snapshot(self.root/'out')['nodes']
        local=[n for n in nodes if n['kind']=='type' and n['name']=='local']
        self.assertEqual(2,len(local)); self.assertEqual(2,len({n['id'] for n in local}))
        self.assertTrue(next(n for n in local if n['path']=='a.c')['citation'].endswith(':L2'))
        self.assertTrue(next(n for n in nodes if n['name']=='BPF_PROG_LOAD')['citation'].endswith(':L3'))

    def test_control_words_do_not_become_function_nodes(self):
        (self.repo/'f.c').write_text('int f(int x) {\n if (x) {\n return 1;\n }\n return 0;\n}\n')
        ingest(self.repo,'fixture',self.root/'out',['*.c'],fixture=True)
        self.assertEqual({'f'},{n['name'] for n in load_snapshot(self.root/'out')['nodes'] if n['kind']=='function'})

    def test_globs_preserve_directory_depth(self):
        self.assertTrue(matches_scope('kernel/bpf/f.c','kernel/bpf/**/*.c'))
        self.assertTrue(matches_scope('kernel/bpf/nested/f.c','kernel/bpf/**/*.c'))
        self.assertFalse(matches_scope('kernel/bpf/nested/f.c','kernel/bpf/*.c'))

    def test_source_tree_filters_scoped_paths_before_loading_blobs(self):
        (self.repo / 'keep.c').write_text('int keep(void) { return 0; }\n')
        (self.repo / 'skip.c').write_text('int skip(void) { return 0; }\n')
        with SourceTree(self.repo, 'fixture', fixture=True, scope=['keep.c']) as source:
            self.assertEqual(['keep.c'], source.paths)
            self.assertEqual(['keep.c'], list(source.blobs))


if __name__ == '__main__': unittest.main()
