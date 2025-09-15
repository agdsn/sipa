[![Code Climate](https://codeclimate.com/github/agdsn/sipa/badges/gpa.svg)](https://codeclimate.com/github/agdsn/sipa)

SIPA - Supreme Information Providing Application
================================================

Name
----

Just as SIPA stands for a ball over the net game[1], the lesser known
**S**upreme **I**nformation **P**roviding **A**pplication does just the same --
sending packets over the internet.

This project is a flask-based webserver developed by members of the student
network Dresden.


Usage
-----

Please note that SIPA has been built to fit our specific purposes.  This means
that there will be features you probably won't need, such as the traffic
monitoring.


How can I run Sipa?
-------------------

> [!CAUTION]
> This information is largely outdated.
> It will be updated once a proper `pyproject.toml` stands and the docker setup has been simplified.

As a general note, you should have `docker` and `docker-compose`
installed.

The simplest method is to run `docker-compose -f build/dev/docker-compose.yml
up -d`.

This should automatically set up an nginx container on port 80
providing `/sipa` and `/sipa_debug`, which are two containers of sipa,
the first running on uwsgi, and the second directly using `sipa.py`.

If this does not work for you see “Running on Docker” below for a
manual (i.e. not docker-compose-based) container setup.
requires [uv](https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion) installed!
To run SIPA wihout Docker you can do the following:

```shell
uv sync
# maybe ask for installing python version then run: uv python install 3.12.11

# Install the dependencies
sudo apt install libpq-dev  # For Debian based distributions
sudo dnf install libpq-devel # For Fedora

# Run SIPA with flask
uv run flask run
```
## Changing Backends
To set a different backend a dot `.env` file can be used. Just `cp example/.env .env` and set the prefered backend.
Backends
- pycroft: is the main Backend for interaction with [pycroft](https://github.com/agdsn/pycroft). Important make sure pycroft is running properly first!!!
- sample: used for easy setup and will be sufficient when just the frontend or presentation is touched

can also be done via just:
```shell
just set sample
# or
just set pycroft
```

## Is there any more documentation?

Sipa provides documentation via sphinx (ergo, docstrings).  At the
moment, there is no automatic pushing
to [here](https://agdsn.github.io/sipa/), so you need to do it locally
by running `make docs` and `make show_docs`, which opens an http
server at `docs/build/html`.

### Editing documentation

The documentation is defined in rst files in `docs/src`.  The largest
part consists of automatic inclusion of module documentation using
`.. automodule::`.


How can I run the tests?
------------------------

```shell
just test
```

Running on Docker
-----------------

### Requirements

Before you start, make sure you have installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)
- ([just](https://just.systems/man/en/) not needed but a nice to have for just using the just file)
### Development Environment (dev)

The development environment is intended for local development.

Start:
`just start dev`

Stop:
`just stop dev`

Access in browser:  http://127.0.0.1:8000

### Test Environment (test-env)

The test environment mirrors the production setup more closely.
It is mainly used for testing JavaScript features that require HTTPS or special headers.

Initial setup:
`just setup test-env`

Start and stop:
- `just start test-env`
- `just stop test-env`

Access in browser
- https://localhost
- http://localhost

The TLS certificate can be found in the `example/` directory.

### Common Issues

Port already in use
Adjust the port in docker-compose.override.yml or in your just commands.

Rebuilding after code changes

`just rebuild SETUP`



### Running with a prefix

If you run sipa under something else than `/`, *make sure you specify this* during `docker run`!

Instead of the default `uwsgi --ini uwsgi.ini`, you will have to use
`uwsgi --ini uwsgi.ini:prefixed --set-ph prefix=/mountpoint`


## Configuration ##

### Environment variables ###

The default config (`sipa.default_config`) reads environment variables
for the most cases.

### Local Python config file ###

If one prefers to write configuration into a file locally, sipa reads
`/config.py`.  If the environment variable `SIPA_CONFIG_FILE` is set,
its path is taken instead.

### Logging ###

In order to provide an additional logfile, set the app's `LOG_CONFIG`
variable in your local configuration file.

It has to be set to a dict usable by `dictConfig()`.  For further
documentation, see [the python docs](https://docs.python.org/3/howto/logging-cookbook.html#an-example-dictionary-based-configuration).

Also, you might want to look into `sipa.defaults.DEFAULT_CONFIG` for the current structure.

Keep in mind you don't need to rewrite the whole default configuration
every time, since you can include `'incremental': True` in said dict.


## Translations

Sipa uses [flask-babel](https://python-babel.github.io/flask-babel/) for
translations.  To update translations, You should have pybabel and
poedit installed (via pip or any other way), and run `make translate`.
Since unfortunately, the build proocess is not automated (or done at
the start), you need to check in the changes to the compiled files
yourself.

Required format for the markdown files
--------------------------------------

In the folder `content/` you can place markdown files to use them as *content
pages* as well as *news*.  The folder structure has to look like this, following
the conditions explained below:

    content
    ├── images
    │   ├── image.png
    │   └── logo.png
    ├── legal
    │   ├── impressum.de.md
    │   ├── impressum.en.md
    │   ├── index.de.md
    │   └── index.en.md
    ├── news
    │   ├── 2015-03-11-new_website.de.md
    │   ├── 2015-03-11-new_website.en.md
    │   ├── index.de.md
    │   └── index.en.md
    └── support
        ├── contacts.de.md
        ├── contacts.en.md
        ├── faq.de.md
        ├── faq.en.md
        ├── index.de.md
        └── index.en.md

The *navigation bar* is built by scanning every directory for `*.md`-files.
Directories containing the latter are then expected to contain an index file for
every language code, e.g. `index.en.md` These index files decide whether it will
appear in the navigation bar and which title it will be displayed with.

The index files have to contain certain metadata in the form `property:
value`. This metadata section is terminated by an empty line (`\n\n`)

* To *not* include a folder in the menu, set `index: false`, as you will need
  for the `news/` folder(!).

* To *include* a folder, set the title of the navigation bar with `name:` as
  well as its position with `rank`.  Do not forget to set `index: true`
  explicitly.

If the parameter `index` does not exist, the corresponding folder will not
appear in the navigation bar, although every folder containing a markdown file
*must* contain an `index.xx.md` file.

The markdown files must have a header in the same fashion as the index files. A
complete .md file can look like this:

    title: Stuff
    author: alice
    date: 2015-03-27
    icon: bi-person

    ### Stuff
    #### Part 1

    To do stuff, you have to do stuff first.

Another possibility is to include hyperlinks, which only have a metadata
section:

    title: Awesome page
    icon: bi-emoji-smile
    link: https://example.org/
    rank: 1

Translations
------------
Make sure you installed `Babel` via pip. Then, just run `make translate`.

[1] https://en.wikipedia.org/wiki/Sipa
