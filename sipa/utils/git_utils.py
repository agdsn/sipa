# -*- coding: utf-8 -*-
from logging import getLogger
from git.exc import GitCommandError
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
