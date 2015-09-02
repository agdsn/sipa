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


[1] https://en.wikipedia.org/wiki/Sipa
