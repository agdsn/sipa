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

As a general note, you should have `docker` and `docker-compose`
installed.

The simplest method is to run `docker-compose -f build/dev/docker-compose.yml
up -d`.

This should automatically set up an nginx container on port 80
providing `/sipa` and `/sipa_debug`, which are two containers of sipa,
the first running on uwsgi, and the second directly using `sipa.py`.

If this does not work for you see “Running on Docker” below for a
manual (i.e. not docker-compose-based) container setup.

To run SIPA wihout Docker you can do the following:

```shell
# Create an venv
python -m venv venv

# Activate the venv
. venv/bin/activate[.fish|.csh]

# Install the dependencies
sudo apt install libpq-dev  # For Debian based distributions
pip install -r requirements.txt

# Run SIPA with flask
flask run
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

For testing, there exists the docker-compose file `build/testing/docker-compose.yml`:

```shell
docker-compose -f build/testing/docker-compose.yml up -d
docker-compose -f build/testing/docker-compose.yml run --rm sipa_testing pytest -v
```

…ore choose any other testing command you wish.  For example, you can
execute a single test case using `nosetests -v
tests.integration.test_hss_ldap:HssLdapPasswordTestCase`

Running on Docker
-----------------

To build the image, `cd` into your instance of sipa (which contains the
`Dockerfile`) and run

```shell
docker build -t sipa .
```

Now, you have basically two possibilities to use sipa:

- Using uwsgi: This is the standard option. Just run:

```shell
docker run --name sipa -d sipa
```

Note that in order to use above example, you have to use another docker
container, i.e. an nginx instance, which is linked to the `sipa` container. If
you don't want to do this, you have to expose port 5000 adding `-p 5000:5000` as
a parameter.

- Using http: This is an option you have to envoke manually. To use it, run

```shell
docker run --name sipa -p 5000:5000 -d sipa python sipa.py --exposed
```

If you want to use sipa for development, adding `--debug` after `sipa.py` and
mounting your sipa folder using `-v <path>:/home/sipa/sipa` is recommended.


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
