import os
from shutil import rmtree
from subprocess import call
from tempfile import mkdtemp, TemporaryDirectory
from unittest import TestCase

from git import Repo

from sipa.utils.git_utils import init_repo, update_repo

SAMPLE_FILE_NAME = "sample_file"
OTHER_FILE_NAME = "other_sample_file"

AUTHOR_NAME = "Test User"
AUTHOR_MAIL = "test@user.nonexistent.onion"


def set_author_config_locally(path=None):
    custom_git_options = ([f"--git-dir={path}"]
                          if path is not None
                          else [])
    git_command_head = ["git", *custom_git_options, "config"]

    call([*git_command_head, "user.name", AUTHOR_NAME])
    call([*git_command_head, "user.email", AUTHOR_MAIL])


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
        set_author_config_locally()

        with open(SAMPLE_FILE_NAME, "w") as f:
            f.write("This is a sample file.")

        call(["git", "add", SAMPLE_FILE_NAME])
        call(["git", "commit", "-m", "'initial commit'", "-q"])

        bare_path = os.path.join(path, f"{name}.git")
        # `git clone --bare` Creates a new bare repo from the existing one.
        # signature: git clone --bare {src} {bare_dest}
        call(["git", "clone", "--bare", tmp_git_dir, bare_path, "-q"])

        os.chdir(old_dir)

    return bare_path


def init_cloned_git_repo(path, path_to_bare):
    """Clone a bare repository into {path}/{name} and return the path."""
    call(["git", "clone", path_to_bare, path, "-q"])


class SampleBareRepoInitializedBase(TestCase):
    """Set up a bare repository in a tmpdir and provide a `Repo` object

    This TestCase provides:
    - The temporary “workdir” (`self.workdir`)
    - The location of the bare repository (`self.repo_path`)
    - The bare repo as a Repo object (`self.repo`)
    """
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
        path = f"{self.workdir}/{self.repo_name}.git"
        assert self.repo_path == path

    def test_repo_path_exists(self):
        """Test that `self.workdir` only contains the bare repo directory"""
        assert os.listdir(self.workdir) == [f"{self.repo_name}.git"]
        assert os.path.isdir(self.repo_path)

    def test_cloned_git_repo_correct_files(self):
        """Test that a clone from the bare repo contains the correct files"""
        cloned_git_path = os.path.join(self.workdir, "test_cloned_instance")
        init_cloned_git_repo(path=cloned_git_path, path_to_bare=self.repo_path)

        # `config` is deleted from the observed files, because it
        # isn't a requirement for this test that it exists, whereas
        # the check _cares_ about whether `.git` exists.
        found_files = set(os.listdir(cloned_git_path)) - {"config"}
        assert found_files, {".git" == SAMPLE_FILE_NAME}

    def test_repo_is_bare(self):
        """Test the repo is bare"""
        self.assertTrue(self.repo.bare)

    def test_repo_only_master(self):
        """Test the repo only has a `master` ref"""
        assert len(self.repo.refs) == 1
        assert self.repo.head.ref.name == "master"


class CorrectlyClonedTesterMixin:
    """A class that provides useful assertions for a cloned repository

    This class expects `self.cloned_repo` to be a Repo object of the
    cloned repository.
    """

    def test_cloned_repo_not_bare(self):
        self.assertFalse(self.cloned_repo.bare)

    def test_cloned_repo_one_branch(self):
        """Test only a `master` exists to which the head points to."""
        assert len(self.cloned_repo.branches) == 1
        assert self.cloned_repo.branches[0].name == "master"
        assert self.cloned_repo.branches[0] == self.cloned_repo.head.ref

    def test_cloned_repo_correct_refs(self):
        # Expected: master(current HEAD), origin/HEAD, origin/master
        assert len(self.cloned_repo.refs) == 3


class ExplicitlyClonedSampleRepoTestBase(SampleBareRepoInitializedBase):
    """A testbase having cloned the sample git directory."""
    def setUp(self):
        super().setUp()
        self.cloned_repo_path = os.path.join(self.workdir, 'cloned')
        init_cloned_git_repo(path=self.cloned_repo_path,
                             path_to_bare=self.repo_path)

        self.cloned_repo = Repo(self.cloned_repo_path)


class InitRepoTestBase(SampleBareRepoInitializedBase):
    """A testbase having initialized a repository using `init_repo`"""
    def setUp(self):
        super().setUp()
        self.cloned_repo_path = os.path.join(self.workdir, 'cloned')
        os.mkdir(self.cloned_repo_path)
        init_repo(repo_dir=self.cloned_repo_path, repo_url=self.repo_path)

        self.cloned_repo = Repo(self.cloned_repo_path)


class TestSampleGitRepositoryCloned(CorrectlyClonedTesterMixin,
                                    ExplicitlyClonedSampleRepoTestBase):
    """Test that manually cloning the bare repository worked correctly"""
    pass


class TestInitRepo(CorrectlyClonedTesterMixin,
                   InitRepoTestBase):
    """Test `init_repo` correctly cloned the bare repository"""
    pass


class TestUpdateRepo(ExplicitlyClonedSampleRepoTestBase):
    def setUp(self):
        super().setUp()

        with TemporaryDirectory() as tmp_git_dir:
            result = call(["git", "clone", "-q", self.repo_path, tmp_git_dir])
            assert result == 0
            tmp_clone = Repo(tmp_git_dir)
            set_author_config_locally(os.path.join(tmp_git_dir, '.git'))

            file_path = os.path.join(tmp_git_dir, OTHER_FILE_NAME)
            with open(file_path, "w") as f:
                f.write("This is a sample file, too.")

            tmp_clone.git.add(file_path)
            tmp_clone.git.commit("-m", "'Other commit'")
            tmp_clone.remote('origin').push()

    def update_repo(self):
        update_repo(self.cloned_repo_path)

    def test_commitsha_different_before_update(self):
        assert self.repo.commit().hexsha != self.cloned_repo.commit().hexsha

    def test_same_commit_after_update(self):
        self.update_repo()
        assert self.repo.commit().hexsha == self.cloned_repo.commit().hexsha
