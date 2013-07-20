#!/usr/bin/python
# coding: utf-8

from os import walk, getcwd, chdir
from os.path import split, normpath, splitext, isdir, isfile, relpath, join, abspath
from random import shuffle
from urllib import quote
import logging
import zipfile
from logging import FileHandler

from flask import Flask, render_template, abort, redirect, send_from_directory, url_for, escape, Markup, make_response

from common import GEXIV_SUPPORT, is_picture, filter_pics, extract_base_meta, subsample_paths, prepare_subsample, config, punymd5

def create_app():

    basedir = getcwd()

    instance = split(split(abspath(__file__))[0])[0]
    app = Flask(__name__, instance_path=instance)
    app.config.from_object('glask.config')

    file_handler = FileHandler(app.config['LOGFILE'])
    app.logger.addHandler(file_handler)
    if not app.config['DEBUG']:
        file_handler.setLevel(logging.WARNING)
    else:
        file_handler.setLevel(logging.DEBUG)

    if not GEXIV_SUPPORT:
        app.logger.warn('GExiv2 is not available, metadata and automatic image rotation disabled')
    app.config['GEXIV_SUPPORT'] = GEXIV_SUPPORT

    app.config['FREEZER_DESTINATION'] = abspath(app.config['FREEZER_DESTINATION'])

    assert isdir(app.config['PICS_DIR']), 'Pictures directory not found'
    assert isdir(app.config['SUBS_DIR']), 'Subsamples directory not found'

    config.PICS_EXTENSIONS = app.config['PICS_EXTENSIONS']
    SUBSAMPLES_SIZES = app.config['SUBSAMPLES_GEOM'].keys()
    if app.config['LINK_ORIGINALS']:
        SUBSAMPLES_SIZES.append('original')

    app.add_template_global(join)

    @app.route('/')
    @app.route('/<path:path>/')
    def tree(path=u''):
        if is_picture(path):
            if app.config['USE_FANCYBOX']:
                return redirect(url_for('picture', size='hi', path=path))
            else:
                return redirect(url_for('view', path=path))
        fixed_path = _sanitize_path(path)
        fixed_path = join(app.config['PICS_DIR'], fixed_path)
        relative_path   = relpath(fixed_path, start=app.config['PICS_DIR'])
        if relative_path == '.': relative_path = ''
        app.logger.debug('relative_path: ' + relative_path)
        tree = walk(fixed_path)
        try:
            (cdir, dirs, files) = tree.next()
        except:
            abort(404)
        finally:
            tree.close()
        pics = filter_pics(files)
        pics.sort()
        pic_titles = _index_view_titles(relative_path, pics)
        dirs.sort(cmp=app.config['ALBUMS_SORT_FUNC'])
        samples = {}
        for d in dirs:
            s = _album_samples(relative_path, d, n=app.config['SAMPLES_COUNT'])
            if len(s) == 0:
                dirs.remove(d)
            else:
                samples[d] = s
        return render_template('index.html',
                dirs=dirs[::-1],
                pics=pics,
                pic_titles=pic_titles,
                samples=samples,
                prefix=relative_path)

    if not app.config['USE_FANCYBOX']:
        @app.route('/<path:path>/view/')
        def view(path):
            fixed_path = _sanitize_path(path)
            if not is_picture(fixed_path) or not isfile(join(app.config['PICS_DIR'], fixed_path)):
                abort(404)
            (prefix, pic) = split(fixed_path)
            prefix += '/'
            return _render_pic_view(prefix, pic)

    @app.route('/<path:path>/raw/<size>.jpg')
    def picture(size='hi', path=''):
        fixed_path = _sanitize_path(path)
        extension = splitext(fixed_path)[1]
        if not extension in app.config['PICS_EXTENSIONS'] or not size in SUBSAMPLES_SIZES:
            abort(404)
        (prefix, pic) = split(fixed_path)
        if not prefix == '':
            prefix += '/'
        if size == 'original':
            if app.config['USE_SENDFILE']:
                return send_from_directory(join(app.instance_path, app.config['PICS_DIR'], prefix),
                        pic, mimetype='image/jpeg')
            else:
                response = make_response()
                response.headers['Content-Type'] = 'image/jpeg'
                internal_url = quote(join(app.config['XACCEL_ORIGINAL'], prefix, pic).encode('utf-8'))
                response.headers['X-Accel-Redirect'] = internal_url
                return response
        else:
            return _serve_subsample(prefix, pic, size)

    if app.config['SERVE_ALBUMS_ARCHIVE']:
        @app.route('/download')
        @app.route('/<path:path>/download')
        def download(path=''):
            fixed_path = _sanitize_path(path)
            prefix, directory = split(join(app.config['PICS_DIR'], path))
            if directory == '':
                prefix = basedir
                directory = app.config['PICS_DIR']

            sent_filename = u'{0}.zip'.format(directory).encode('utf-8')
            archive_name = '{0}.zip'.format(punymd5(directory))
            archive_path = join(app.config['SUBS_DIR'], archive_name)
            if not isfile(archive_path):
                zip = zipfile.ZipFile(archive_path, 'w')
                try:
                    chdir(prefix)
                    for root, dirs, files in walk(path):
                        pics = filter_pics(files)
                        for p in pics:
                            zip.write(join(root, p))
                finally:
                    chdir(basedir)
                    zip.close()
            return send_from_directory(join(app.instance_path, app.config['SUBS_DIR']),
                    archive_name,
                    as_attachment=True,
                    attachment_filename=sent_filename)

    @app.route('/dynamic.css')
    def dynamic_css():
        response = make_response()
        response.headers['Content-Type'] = 'text/css'
        response.data = render_template('dynamic.css')
        return response

    @app.template_filter('tobc')
    def path_to_breadcrumbs(path):
        if path == '':
            return ''
        p = normpath(path)
        dirs = p.split('/')
        part_path = ''
        p = u''
        for d in dirs:
            part_path = join(part_path, d)
            p += u' &rsaquo; <a href="{0}">{1}</a>'.format(
                    escape(url_for('tree', path=part_path)),
                    escape(d))
        return Markup(p)

    def _sanitize_path(path):
        fixed_path = normpath(u'/'+path)[1:]
        if fixed_path != path:
            abort(403)
        return fixed_path

    def _index_view_titles(relative_path, pics):
        prefix = join(app.config['PICS_DIR'], relative_path)
        pic_titles = {}
        for p in pics:
            title = ""
            if GEXIV_SUPPORT:
                src_file = join(prefix, p)
                meta = extract_base_meta(src_file, as_dict=True, as_string=True)
                fnumber = meta.get('fnumber') and 'f/{0}'.format(meta['fnumber'])
                expo    = meta.get('expo')    and '  {0}s'.format(meta['expo'])
                focal   = meta.get('focal')   and '  {0}mm'.format(meta['focal'])
                time    = meta.get('time')    and '  @  {0}'.format(meta['time'])
                title = u'{0}{1}{2}{3}'.format(fnumber, expo, focal, time)
            pic_titles[p] = title
        return pic_titles

    def _album_samples(relative_path, dir, n=10):
        samples = []
        walk_root = join(app.config['PICS_DIR'], relative_path, dir)
        tree = walk(walk_root)
        try:
            while True:
                (cdir, dirs, files) = tree.next()
                if len(files) > 0:
                    pics = filter_pics(files)
                    shuffle(pics)
                    for i in range(len(pics)):
                        pics[i] = relpath(join(cdir, pics[i]), start=app.config['PICS_DIR'])
                    samples.extend(pics[:(n-len(samples))])
                    if len(samples) == n:
                        break
                shuffle(dirs)
        except Exception, e:
            pass
        finally:
            tree.close()
        app.logger.debug(u'samples for {0} [{1}]\n{2}'.format(dir, walk_root, samples))
        return samples

    def _render_pic_view(prefix, pic):
        src_directory = join(app.config['PICS_DIR'], prefix)
        if GEXIV_SUPPORT:
            meta = extract_base_meta(src_directory + pic, as_dict=True)
            if meta['fnumber']:
                meta['fnumber'] = meta['fnumber'].replace('F',u'f /')
        else:
            meta = None
        tree = walk(src_directory)
        (cdir, dirs, pics) = tree.next()
        pics.sort()
        i = pics.index(pic)
        prev = None
        next = None
        if i > 0:
            prev = pics[i-1]
        if i < len(pics)-1:
            next = pics[i+1]
        return render_template('view.html',
                prefix=prefix,
                pic=pic,
                meta=meta,
                previous=prev,
                next=next)

    def _serve_subsample(prefix, pic, size):
        (src_file, dst_dir, dst_file) = subsample_paths(prefix, pic)
        dst_file = dst_file.format(size=size)
        if not isfile(src_file):
            abort(404)
        prepare_subsample(src_file, dst_dir, dst_file, size)

        if app.config['USE_SENDFILE']:
            return send_from_directory(join(app.instance_path, dst_dir), dst_file, mimetype='image/jpeg')
        else:
            # tell nginx to server the file and where to find it
            response = make_response()
            response.headers['Content-Type'] = 'image/jpeg'
            response.headers['X-Accel-Redirect'] = join(app.config['XACCEL_THUMBS'], dst_dir, dst_file)
            return response

    return app
