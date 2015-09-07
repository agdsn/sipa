# -*- coding: utf-8 -*-
import git


def init_repo(repo_dir, repo_url):
    repo = git.Repo.init(repo_dir)
    if repo.remotes:
        origin = repo.remote('origin')
    else:
        origin = repo.create_remote('origin', repo_url)
    origin.fetch()
    repo.git.reset('--hard', 'origin/master')


def update_repo(repo_dir):
    repo = git.Repo.init(repo_dir)
    if repo.commit().hexsha != repo.remote().fetch()[0].commit.hexsha:
        origin = repo.remote()
        origin.fetch()
        repo.git.reset('--hard', 'origin/master')
        return True
    else:
        return False
