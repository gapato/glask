# Debug mode
DEBUG = True

# Where to log stuff
LOGFILE = u'logs/glask.log'

# Whether flask should serve static files itself
# If false, your webserver handles this (currently only
# nginx is supported, via XACCEL_REDIRECT).
USE_SENDFILE = True

# nginx URL prefixes to serve pictures
#
# thumbnails
XACCEL_THUMBS   = u'/t'
# full size
XACCEL_ORIGINAL = u'/o'

# options for the static build (frozen_flask)
#
# the baseurl, your gallery will be available at FREEZER_BASE_URL.
FREEZER_BASE_URL = u'http://localhost/'

# The directory where the site will be built, relative to the directory
# containing glask/, run.py, manage.py, etc.
# Data unrelated to glask will be lost
FREEZER_DESTINATION = u'build'

# Silence mimetypes mismatch errors
FREEZER_IGNORE_MIMETYPE_WARNINGS = True

# Don't keep old files
# (ie file that would not be generated from a fresh build)
FREEZER_REMOVE_EXTRA_FILES = True

# Only consider these file extensions as pictures
PICS_EXTENSIONS = [ u'.jpg', u'.jpeg', u'.JPG', u'.JPEG' ]

# Where pictures are stored, should be readable by flask/your webserver
PICS_DIR     = u'photos'

# Where smaller, generated versions of the pictures will be stored,
# should be writtable by flask/your webserver
SUBS_DIR     = u'subsamples'

# Size of thumbnails (lo, in lists of pictures) and view size (hi) pictures
SUBSAMPLES_GEOM = {
    u'tiny'     : (200,48),
    u'lo'       : (1000,200),
    u'hi'       : (1600,800),
}

SAMPLES_COUNT = 5

# Whether to offer the option to download a whole directory
# as a .zip archive
SERVE_ALBUMS_ARCHIVE = True

# Whether to use Fancybox. If False, use a seperate page
# to view single pictures.
USE_FANCYBOX = True

# Whether to show a frame in picture lists
FRAME_ALBUM_VIEW = False

# Whether to serve the original picture
LINK_ORIGINALS = True

# Theme, 'dark' or 'light'
THEME = 'dark'

# Notice, to appear in the top right-hand corner
NOTICE = 'Glask'

# Which comparison function to use when sorting albums
# Takes 2 parameters, which are album names (directory names)
# Must return -1, 0 or 1.
ALBUMS_SORT_FUNC = None
