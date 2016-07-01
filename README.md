[![Build Status](https://travis-ci.org/agdsn/sipa.svg?branch=develop)](https://travis-ci.org/agdsn/sipa)

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
monitoring or splitting the login process into certain divisions.


How can I run Sipa?
-------------------

As a general note, you should have `docker` and `docker-compose`
installed.  Just using python and e.g. a virtualenv is possible, but
discouraged.

The simplest method is to run `docker-compose -f build/development.yml
up -d`.

This should automatically set up an nginx container on port 80
providing `/sipa` and `/sipa_debug`, which are two containers of sipa,
the first running on uwsgi, and the second directly using `sipa.py`.

If this does not work for you see “Running on Docker” below for a
manual (i.e. not docker-compose-based) container setup.


How can I run the tests?
------------------------

For testing, there exists the docker-compose file `build/testing.yml`:

```shell
docker-compose -f build/testing.yml up -d
docker-compose -f build/testing.yml run --rm sipa_testing python manage.py test
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


## Running with a prefix

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
    glyphicon: glyphicon-user

    ### Stuff
    #### Part 1

    To do stuff, you have to do stuff first.

Another possibility is to include hyperlinks, which only have a metadata
section:

    title: Awesome page
    glyphicon: glyphicon-tower
    link: http://http://www.awesome-page.com/
    rank: 1


Adding dynamic content
----------------------

Sipa is capable of parsing a `json` file to provide “dynamic” content,
i.e. content which varies according to the dormitory selected.

For each content file, Sipa tries to open a file following the naming
scheme `<pagename>.<locale>.json`. If it does not exist or does not
contain valid json, this is ignored and no additional block is
displayed on the webpage.

The file has to follow the format below:

```json
{
    "title": "Financial data",
    "keys": {
        "beneficiary": "Beneficiary",
        "iban": "IBAN",
        "bank": "Bank",
        "bic": "BIC",
        "information": "Information"
    },
    "values": {
        "wu": {
            "beneficiary": "Studentenrat TUD - AG DSN",
            "bank": "Ostsächsische Sparkasse Dresden",
            "iban": "DE61850503003120219540",
            "bic": "OSDD DE 81 XXX",
            "information": "User-ID, Last Name, First Name, Dormitory / Room number"
        },
        "gerok": {
            "beneficiary": "Studentenrat TUD - AG DSN",
            "bank": "Ostsächsische Sparkasse Dresden",
            "iban": "To be investigated",
            "bic": "To be investigated",
            "information": "To be investigated"
        },
        "local": {
            "beneficiary": "Not available",
            "bank": "Not available",
            "iban": "Not available",
            "bic": "Not available",
            "information": "Not available"
        }
    },
    "mappings": {
        "wu": "wu",
        "zw": "wu",
        "borsi": "wu",
        "gerok": "gerok",
        "localhost": "local"
    }
}
```

Because information may or may not dependend on a data source, it can
be grouped using `mappings`. Dormitories whose name is not specified
in `mappings` will not appear in the `select` field on the web page,
so be careful to keep the list complete.

The value of a `mappings` field has to correspond to a dataset in `values`.



[1] https://en.wikipedia.org/wiki/Sipa
