# -*- coding: utf-8 -*-
from datetime import datetime
from flask.ext.babel import format_datetime
from git.exc import GitCommandError, InvalidGitRepositoryError, CacheError
from logging import getLogger
import git

logger = getLogger(__name__)


def init_repo(repo_dir, repo_url):
    repo = git.Repo.init(repo_dir)
    if repo.remotes:
        origin = repo.remote('origin')
    else:
        origin = repo.create_remote('origin', repo_url)
    origin.fetch()
    repo.git.reset('--hard', 'origin/master')
    logger.info("Initialized git repository %s in %s", repo_dir, repo_url)


def update_repo(repo_dir):
    repo = git.Repo.init(repo_dir)

    try:
        if repo.commit().hexsha != repo.remote().fetch()[0].commit.hexsha:
            origin = repo.remote()
            origin.fetch()
            repo.git.reset('--hard', 'origin/master')
            return True
        else:
            return False
    except GitCommandError:
        logger.error("Git fetch failed.", exc_info=True, extra={'data': {
            'repo_dir': repo_dir
        }})
    else:
        logger.info("Fetched git repository", extra={'data': {
            'repo_dir': repo_dir
        }})


def get_repo_active_branch(repo_dir):
    """
    :param repo_dir: path of repo
    :type repo_dir: str
    :return: name of currently checked out branch
    :rtype: str
    """
    try:
        sipa_repo = git.Repo(repo_dir)
        return sipa_repo.active_branch.name
    except TypeError:  # detatched HEAD
        return "@{}".format(sipa_repo.head.commit.hexsha[:8])


def get_latest_commits(repo_dir, commit_count):
    """
    :param repo_dir: path of repo
    :type repo_dir: str
    :param commit_count: number of commits to return
    :type commit_count: int
    :return: commit information (hash, message, author, date) about
    commit_count last commits
    :rtype: list of dicts
    """
    try:
        sipa_repo = git.Repo(repo_dir)
        commits = sipa_repo.iter_commits(max_count=commit_count)
        return [{
            'hexsha': commit.hexsha,
            'message': commit.summary,
            'author': commit.author,
            'date': format_datetime(datetime.fromtimestamp(
                commit.committed_date)),
        } for commit in commits]
    except (InvalidGitRepositoryError, CacheError, GitCommandError):
        logger.exception("Could not get latest commits", extra={'data': {
            'repo_dir': repo_dir}})
        return []
