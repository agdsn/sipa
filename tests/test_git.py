# -*- coding: utf-8; -*-

import os
from shutil import rmtree
from subprocess import call
from tempfile import mkdtemp, TemporaryDirectory
from unittest import TestCase

from git import Repo


SAMPLE_FILE_NAME = "sample_file"


def init_sample_git_repo(path, name):
    """Initialize a bare git repository with one commit.

    The commit adds a test file.

    :param path: The (existing) path which will contain the repository directory
    :param name: The name which will used to name the bare repository ("{name}.git")
    :return: The path of the bare git repository
    """
    path = os.path.abspath(path)
    old_dir = os.getcwd()
    with TemporaryDirectory() as tmp_git_dir:
        os.chdir(tmp_git_dir)
        call(["git", "init", "-q"])

        with open(SAMPLE_FILE_NAME, "w") as f:
            f.write("This is a sample file.")

        call(["git", "add", SAMPLE_FILE_NAME])
        call(["git", "commit", "-m", "'initial commit'", "-q"])

        bare_path = os.path.join(path, "{}.git".format(name))
        # `git clone --bare` Creates a new bare repo from the existing one.
        # signature: git clone --bare {src} {bare_dest}
        call(["git", "clone", "--bare", tmp_git_dir, bare_path, "-q"])

        os.chdir(old_dir)

    return bare_path


def init_cloned_git_repo(path, path_to_bare):
    """Clone a bare repository into {path}/{name} and return the path."""
    call(["git", "clone", path_to_bare, path, "-q"])


class SampleBareRepoInitializedBase(TestCase):
    def setUp(self):
        self.workdir = mkdtemp()
        self.repo_name = "test"
        self.repo_path = init_sample_git_repo(self.workdir, self.repo_name)
        self.repo = Repo(self.repo_path)

    def tearDown(self):
        rmtree(self.workdir)


class TestSampleGitRepository(SampleBareRepoInitializedBase):
    """Tests concerning the result of `init_sample_git_repo`"""
    def test_repo_path_correctly_joined(self):
        path = "{}/{}.git".format(self.workdir, self.repo_name)
        self.assertEqual(self.repo_path, path)

    def test_repo_path_exists(self):
        """Test that `self.workdir` only contains the bare repo directory"""
        self.assertEqual(os.listdir(self.workdir),
                         ["{}.git".format(self.repo_name)])
        self.assertTrue(os.path.isdir(self.repo_path))

    def test_cloned_git_repo_correct_files(self):
        """Test that a clone from the bare repo contains the correct files"""
        cloned_git_path = os.path.join(self.workdir, "test_cloned_instance")
        init_cloned_git_repo(path=cloned_git_path, path_to_bare=self.repo_path)

        self.assertEqual(set(os.listdir(cloned_git_path)),
                         {".git", SAMPLE_FILE_NAME})

    def test_repo_is_bare(self):
        """Test the repo is bare"""
        self.assertTrue(self.repo.bare)

    def test_repo_only_master(self):
        """Test the repo only has a `master` ref"""
        self.assertEqual(len(self.repo.refs), 1)
        self.assertEqual(self.repo.head.ref.name, 'master')


class TestSampleClonedRepositoryBase(SampleBareRepoInitializedBase):
    """A class that provides useful assertions for a cloned repository"""
    def setUp(self):
        super().setUp()
        self.cloned_repo_path = os.path.join(self.workdir, 'cloned')

    def assert_cloned_repo_not_bare(self):
        self.assertFalse(self.cloned_repo.bare)

    def assert_cloned_repo_one_branch(self):
        """Test only a `master` exists to which the head points to."""
        self.assertEqual(len(self.cloned_repo.branches), 1)
        self.assertEqual(self.cloned_repo.branches[0].name, 'master')
        self.assertEqual(self.cloned_repo.branches[0], self.cloned_repo.head.ref)

    def assert_cloned_repo_correct_refs(self):
        # Expected: master(current HEAD), origin/HEAD, origin/master
        self.assertEqual(len(self.cloned_repo.refs), 3)

    def assert_repo_correctly_cloned(self):
        self.assert_cloned_repo_not_bare()
        self.assert_cloned_repo_one_branch()
        self.assert_cloned_repo_correct_refs()


class TestSampleGitRepositoryCloned(TestSampleClonedRepositoryBase):
    def setUp(self):
        super().setUp()
        init_cloned_git_repo(path=self.cloned_repo_path,
                             path_to_bare=self.repo_path)
        self.cloned_repo = Repo(self.cloned_repo_path)

    def test_repo_correctly_cloned(self):
        self.assert_repo_correctly_cloned()
