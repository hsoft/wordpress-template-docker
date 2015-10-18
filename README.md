# Wordpress website template powered by Docker

This is a template for a Wordpress website powered by [Docker][docker] through the
[docker-map][docker-map] library. The goal is to be quickly up-and-running when starting
the development of a new Wordpress website or inheriting an old one.

## Current status

This template is currently in development. For now, its capabilities are rather limited as it only
launches a vanilla newborn wordpress sites. The goal is to eventually support live theme/plugin
editing, plugin dependencies installation, easy import of legacy Wordpress sites into the template,
etc..

## Requirements

* [sudo-less][sudoless-docker] [Docker][docker]
* Python 3.4+

## Starting a new project

This project is designed to be copied every time you start (or inherit) a new Wordpress project.

### Step 1: Clone the project

First, clone this git repo somewhere. This new git repo will host your new project (themes,
plugins, etc.).

### Step 2: Configure the project

Open the `cmds.py` file. At the top of the file are the config constants. The `PROJECT_NAME` one
is the most important. It determines the name of all your docker images and containers, database
name, etc.

Make sure that `WORDPRESS_VERSION` and `WORDPRESS_MD5` are up to date.

### Step 3: Make images

When at the root of the project, run `./manage --verbose make` to build your two images (one with
a MariaDB server and the other with Wordpress under Apache).

### Step 4: Run the website

Then, it's only a matter of running `./manage start` to run the server, which is accessible at
`http://localhost`. You will then be prompted with the standard Wordpress site creation dialog.
Note that the usual "Database configuration" dialog is skipped because the `wp-config.php` file
was already created during the `make` phase.

You can stop the server with `./manage stop`. If you want to get rid of your data, do
`./manage stop --clean` which will remove all containers and their associated volumes.

## Managing persistent data

TODO

## Inheriting a legacy Wordpress site

TODO

## Why not docker-compose?

The tool of choice these days seems to be [docker-compose][docker-compose], which is very easy to
set up and much less boiler-plate than what we have here. However, this is at the cost of
flexibility. I find that docker-compose's elegance drops off quickly in some situations.

The advantage of docker-map is that it's a library. As a use of that library, we have all the
flexibility we need to work around unforseen situations in an elegant manner.

[docker]: https://www.docker.com/
[docker-map]: https://github.com/merll/docker-map
[sudoless-docker]: http://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo
[docker-compose]: https://docs.docker.com/compose/

