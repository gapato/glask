from hashlib import md5
from os import makedirs
from os.path import splitext, isfile, isdir, getmtime, join

import kaa.imlib2 as il2

import config

try:
    from gi.repository import GExiv2
    GEXIV_SUPPORT = True
    GExiv2.log_set_level(GExiv2.LogLevel.MUTE)
except:
    GEXIV_SUPPORT = False

class GExivNotAvailable(Exception):
    pass

pics_extensions = [ u'.jpg', u'.jpeg', u'.JPG', u'.JPEG' ]

def is_picture(path):
    e = splitext(path)[1]
    return e in pics_extensions

def filter_pics(files):
    pics = []
    for f in files:
        if is_picture(f):
            pics.append(f)
    return pics

def fix_img_orientation(img, orientation):
    if not GEXIV_SUPPORT:
        raise GExivNotAvailable()
    if orientation == GExiv2.Orientation.ROT_90:
        img.orientate(1)
    if orientation == GExiv2.Orientation.ROT_180:
        img.orientate(2)
    if orientation == GExiv2.Orientation.ROT_270:
        img.orientate(3)

def extract_base_meta(src_file, as_dict=False, as_string=False):
    if not GEXIV_SUPPORT:
        raise GExivNotAvailable()
    img_meta = GExiv2.Metadata(src_file)
    meta = { 'time' : None }
    if not img_meta.has_exif:
        if as_dict:
            return meta
        else:
            return (None, None)
    meta['time']    = img_meta.get_date_time()
    focal           = int(img_meta.get_focal_length())
    if focal == -1: focal = None
    meta['focal']   = focal
    meta['expo']    = img_meta.get_exposure_time()
    meta['fnumber'] = img_meta.get_tag_interpreted_string('Exif.Photo.FNumber')
    if as_dict:
        if as_string:
            meta['time']    = meta.get('time') and meta['time'].strftime('%d/%m/%Y') or ''
            meta['focal']   = meta.get('focal') and str(meta['focal']) or ''
            meta['expo']    = meta.get('expo') and str(meta['expo']) or ''
            meta['fnumber'] = meta.get('fnumber') and str(meta['fnumber']).replace('F', '') or ''
        return meta
    orientation = img_meta.get_orientation()
    img_meta.clear()
    if meta['time']:
        img_meta.set_date_time(meta['time'])
    if meta['focal']:
        img_meta.set_exif_tag_long('Exif.Photo.FocalLength', meta['focal'])
    if meta['expo']:
        img_meta.set_exif_tag_rational('Exif.Photo.ExposureTime', meta['expo'])
    if meta['fnumber']:
        img_meta.set_exif_tag_string('Exif.Photo.FNumber', meta['fnumber'])
    return (img_meta, orientation)

def subsample_paths(prefix, pic):
    src_file = join(config.PICS_DIR, prefix, pic)
    (base, ext) = splitext(pic)
    dst_file = '{0}.{{size}}{1}'.format(
            punymd5(join(prefix, pic)),
            ext.lower())
    dst_dir = join(config.SUBS_DIR, dst_file[:2])
    return (src_file, dst_dir, dst_file)

def prepare_subsample(src_file, dst_dir, dst_file, sizes, force=False):
    """ Scale an image, fixing orientation

    Metadata will be removed, if size is 'hi' the following
    info will be preserved:
    * Date taken
    """
    if sizes.__class__ in [str, unicode] :
        assert sizes in config.SUBSAMPLES_GEOM.keys()
        sizes = [sizes]
    size_info = {}
    for s in sizes:
        formatted_dst_file = dst_file.format(size=s)
        size_info[s] = {
                    'todo'     : force,
                    'dst_path' : join(dst_dir, formatted_dst_file),
                    'dst_file' : formatted_dst_file
                }
        if not isfile(size_info[s]['dst_path']):
            size_info[s]['todo'] = True
        elif getmtime(size_info[s]['dst_path']) < getmtime(src_file):
            size_info[s]['todo'] = True
        else:
            continue
        if not isdir(dst_dir):
            makedirs(dst_dir)
    for s in sizes:
        if not size_info[s]['todo']:
            size_info.pop(s)
    if len(size_info) > 0:
        with file(src_file) as buf:
            img = il2.open_from_memory(buf.read())

            if GEXIV_SUPPORT:
                (slim_meta, orientation) = extract_base_meta(src_file)
                fix_img_orientation(img, orientation)

            for s in size_info:
                if len(size_info) > 1:
                    img_new = img.copy()
                else:
                    img_new = img
                img_new.thumbnail(config.SUBSAMPLES_GEOM[s])
                img_new.save(join(dst_dir, size_info[s]['dst_file']))
                if GEXIV_SUPPORT and slim_meta != None and s == 'hi':
                    slim_meta.save_file(size_info[s]['dst_path'])

def punymd5(string):
    return md5(string.encode('punycode')).hexdigest()
