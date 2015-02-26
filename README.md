# Octopus

Octopus is a tool to retrieve information, which is publicly available on the Internet,
about free software projects.

This tool is a reboot of the old [Octopus](http://git.libresoft.es/octopus/) developed
by Carlos Carcia Campos at the Universidad Rey Juan Carlos, Madrid (Spain).

## License

Licensed under GNU General Public License (GPL), version 3 or later

## Download

* Home page: https://github.com/MetricsGrimoire/Octopus
* Releases: https://github.com/MetricsGrimoire/Octopus/releases
* Latest version: https://github.com/MetricsGrimoire/Octopus.git

## Requirements

* Python >= 2.7.5
* MySQL >= 5.5
* SQLAlchemy >= 0.8.2
* Python requests >= 1.2.3
* github3.py >= 1.0.0a1

## Installation

Locally:
    # setup.py install
In the system:
    # sudo setup.py install

## Running Octopus

First, create database as follows:
    # CREATE DATABASE <databasename> CHARACTER SET utf8 COLLATE utf8_unicode_ci;

Run Octopus as follows:
    # $ octopus -u <dbuser> -p <dbpassword> -d <dbname> puppet https://forgeapi.puppetlabs.com
    # $ octopus -u <dbuser> -p <dbpassword> -d <dbname> github --gh-token XXXXX <owner> [<repository>]

## Contact

* Mailing list at https://lists.libresoft.es/listinfo/metrics-grimoire
* IRC channel in freenode #metrics-grimoire
