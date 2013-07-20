# Glask

Glask is a very simple web gallery, written in Python using the Flask framework. It copies the structure of the filesystem in a attempt to be autonomous and minimizing unecessary setup when adding photos. There is basic support for metadata handling and display, depending on GExiv, and thumbnails are generated automaticaly via imlib2. It is also possible to generate a static version of the gallery for use on hosts the do not provide Python support.

Glask is licensed under the WTFPL, which means it is effectively in the public domain.

## Getting started

### Dependencies

First you need to make sure you have the right dependencies:

#### Required:

* `python` >= 2.6 (not tested on python 3.x)
* `Flask`
* `imlib2`, along with the `kaa-base` and `kaa-imlib2` python bindings

#### Optional:

* `Frozen-flask` if you want to generate a static site
* `GExiv2` for metadata handling

### App structure

    ├── manage
    ├── run
    ├── doc/
    ├── glask/
    │   ├── app.py
    │   ├── common.py
    │   ├── config.py (!)
    │   ├── config-default.py
    │   ├── layout/
    │   ├── static/
    │   └── templates/
    ├── photos/
    └── subsamples/

The `photos` directory is where your pictures are stored. It should be readable by your app server and webserver. The `subsamples` directory is where generated, smaller version of the pictures will be stored, you need to create it and make sure it is writtable by the app/webserver. The location of both of these can be changed in your `glask/config.py` file, with you need to create &ndash; starting from the provided defaults file is probably a good idea, it has some basic documentation of configuration options.

To start the app, simply run `python run`. The `manage` CLI tool allows you to regenerated thumbnails without a browser (`thumbs` command) and to generate a static site (`freeze` command)

The `doc` directory contains sample configuration files for your webserver, currently only Nginx. If you're running another one, consider contributing a sample for it.

## Bundled software/artwork

* jQuery
* FancyBox
* GlyphIcons

## License

WTFPL, see LICENSE.txt
