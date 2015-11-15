# -*- coding: utf-8 -*-
from logging import getLogger
from git.exc import GitCommandError
from datetime import datetime
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
    except:
        logger.error("Could not get active branch", extra={'data': {
            'repo_dir': repo_dir}})
        return 'repo problem'


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
        commits = list(sipa_repo.iter_commits(get_repo_active_branch(repo_dir),
                                              max_count=commit_count))
        return [{'hexsha': commit.hexsha,
                 'message': commit.message,
                 'author': commit.author,
                 'date': datetime.fromtimestamp(int(commit.committed_date))
                 .strftime('%Y-%m-%dT' '%H:%M'),
                 } for commit in commits]
    except:
        logger.error("Could not get latest commits", extra={'data': {
            'repo_dir': repo_dir}})
        return []
