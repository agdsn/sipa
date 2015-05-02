SIPA - Supreme Information Providing Application
==================================


Name
----------------------------------
Just as SIPA stands for a ball over the net game[1], the lesser known **s**upreme **i**nformation **p**roviding **a**pplication
does just the same -- sending packets over the internet.

This project is a flask-based webserver developed by members of the student network Dresden.

Usage / Forking
----------------------------------
As the project is
* not modularized in its current state,
* strongly depends on our infrastructure
* has been designed for our purposes (e.g. view each user's specific data)
it is not suitable for any custom use.

Note that **this will change soon**, because we plan to use sipa elsewhere.


Libraries required to run dev server
----------------------------------

Debian packages:
`apt-get install libldap2-dev libffi-dev libsasl2-dev libxml2-dev libxslt1-dev libmysqlclient-dev libpython2.7-dev`


Required format for the markdown files
----------------------------------
In the folder `content/` you can place markdown files to use them as *content pages* as well as *news*.
The folder structure has to look like this, following the conditions explained below:

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
 Directories containing the latter are then expected to contain an index file for every language code, e.g. `index.en.md`
 These index files decide whether it will appear in the navigation bar and which title it will be displayed with.
 
The index files have to contain certain metadata in the form `property: value`. This metadata section is terminated by an empty line (`\n\n`)
* To *not* include a folder in the menu, set `index: false`, as you will need for the `news/` folder(!).
* To *include* a folder, set the title of the navigation bar with `name:` as well as its position with `rank`.
 Do not forget to set `index: true` explicitly.
 
If the parameter `index` does not exist, the corresponding folder will not appear in the navigation bar, although every folder containing a markdown file *must* contain an `index.xx.md` file.

The markdown files must have a header in the same fashion as the index files. A complete .md file can look like this:

    title: Stuff
    author: alice
    date: 2015-03-27
    glyphicon: glyphicon-user
    
    ### Stuff
    #### Part 1
    
    To do stuff, you have to do stuff first.

Another possibility is to include hyperlinks, which only have a metadata section:

    title: Awesome page
    glyphicon: glyphicon-tower
    link: http://http://www.awesome-page.com/
    rank: 1

Running on Docker
-----------------
To create a running instance of Sipa with Docker, you have to create the *image*
first. This is determined by the Dockerfile, which is located in the top folder
of the repository, in this case `.`.
Therefore, you have to run `docker build -t sipa-base .` in order to create a
valid docker image; “sipa-base” is an arbitrary name we chose to make
identification easier. Else, `docker images` would just print
the ID of the image.
To use Sipa, you have to run a container based on that image. Additionally, you
will want to:

* mount the top directory to apply changes in that directory (crucial for
  development)
* make the according tcp port accessible for you (i.e. `:5001`)
* give the container a name (i.e. `sipa`)
* run the server (via `python`)

This leads to the following command:

```shell
docker run --rm \
    --name=sipa \
    -p=5001:5000 \
    -v=/home/lukas/code/sipa:/home/sipa/sipa \
    sipa-base \
    python sipa.wsgi
```

[1] https://en.wikipedia.org/wiki/Sipa
