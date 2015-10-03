#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from base64 import b64encode
from hashlib import sha1
import datetime
import hashlib
import hmac
import os
import re
import socket
import struct
import urllib
import urlparse
import uuid
from decimal import Decimal

from attrdict import AttrDict
from flask import request, current_app
from html2text import HTML2Text
import jwt
import simplejson as json

from base import constant as const
from base import logger
from base.cache import cache
from etc import config


def split_list(lst, n_part):
    "not keep continuess"
    return [lst[i::n_part] for i in xrange(n_part)]


def text2html(text):
    return '<p>%s</p>' % (text.replace('\r', '')
                          .replace('\n\n', '</p><p>')
                          .replace('\n', '<br/>')
                          .replace(' ', '&nbsp;'))


def safe_json_default(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, Decimal):
        return float(obj)

    return str(obj)


def safe_json_dumps(obj, encoding=None, silent=True):
    """
    Encode a Python object to JSON formatted string.

    @params object: Python object
    @params encoding: the character encoding for str instances, default is UTF-8.
    @params silent: not raise error, default is True

    @return: a JSON formatted string if dumps success or None

    """
    kwargs = {"default": safe_json_default}
    if encoding is not None:
        kwargs["encoding"] = encoding

    try:
        str = json.dumps(obj, **kwargs)
    except (ValueError, TypeError):
        if silent:
            return None
        raise

    return str


def safe_inet_ntoa(n):
    """
    Convert numerical ip to string ip(like: 2071801890 -> "123.125.48.34"),
    return None if failed.
    """
    try:
        ip = socket.inet_ntoa(struct.pack(">L", n))
    except (struct.error, socket.error):
        return None

    return ip


def safe_inet_aton(ip):
    """
    Convert string ip to numerical ip(like: "123.125.48.34" -> 2071801890),
    return None if failed.
    """
    try:
        n = struct.unpack(">L", socket.inet_pton(socket.AF_INET, ip))[0]
    except (struct.error, socket.error, AttributeError):
        return None

    return n


def get_day_begin_time(time):
    """
    @params time: datatime

    @return: datetime, begin time of a day
    """
    return time.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end_time(time):
    """
    @params time: datetime

    @return: datetime, end time of a day
    """
    return time.replace(hour=23, minute=59, second=59, microsecond=0)


def safe_strptime(data, format="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.datetime.strptime(data, format)
    except:
        return None


def safe_strpdate(data):
    parsed = safe_strptime(data, "%Y-%m-%d")
    return None if parsed is None else parsed.date()


def safe_strftime(data, format="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.datetime.strftime(data, format)
    except:
        return None


def safe_strfdate(data):
    parsed = safe_strftime(data, "%Y-%m-%d")
    return None if parsed is None else parsed


def url_append(url, nodup=True, **kwargs):
    old_params = urlparse.urlparse(url)[4]
    if nodup and old_params:
        buf = urlparse.parse_qs(old_params)
        for k in buf:
            if k in kwargs:
                kwargs.pop(k)

    if len(kwargs) < 1:
        return url

    params = urllib.urlencode(kwargs)
    if old_params:
        return url + "&" + params
    else:
        return url + "?" + params


def encode_unicode_json(obj, encoding):
    """
    Translate unicode obj into local encoding, usage may be:
      1. json loads return a obj which all str is unicode, encode it to our encoding.
      2. other json like obj can use this func too. ex: form_check
    """

    if isinstance(obj, unicode):
        return obj.encode(encoding)
    elif isinstance(obj, list):
        return [encode_unicode_json(v, encoding) for v in obj]
    elif isinstance(obj, dict):
        return dict([(encode_unicode_json(k, encoding), encode_unicode_json(v, encoding))
                     for k, v in obj.iteritems()])

    return obj


def to_unicode(data, encoding="utf-8"):
    """convert data from some encoding to unicode
    data could be string, list, tuple or dict
    that contains string as key or value
    """
    if data is None:
        return unicode('')

    if isinstance(data, unicode):
        return data

    if isinstance(data, (list, tuple)):
        u_data = []
        for item in data:
            u_data.append(to_unicode(item, encoding))

    elif isinstance(data, dict):
        u_data = {}
        for key in data:
            u_data[to_unicode(key, encoding)] = to_unicode(data[key], encoding)

    elif isinstance(data, str):
        u_data = unicode(data, encoding, 'ignore')
    else:
        u_data = data

    return unicode(u_data)


class UObj:
    # do not gen UObj when input obj type is in base_types
    base_types = (
        bool, float, int, long, complex, unicode,
    )
    # do not gen UObj when attr name in raw_attrs
    raw_attrs = (
        '__name__', '__coerce__',
    )
    # gen UObj with fake rop when input obj doesn't have the attr and
    # attr is in rops
    rops = (
        '__radd__', '__rdiv__', '__rmod__', '__rmul__', '__rsub__',
        '__rand__', '__rlshift__', '__ror__', '__rrshift__', '__rxor__',
        '__rdivmod__', '__rpow__',
    )

    def __init__(self, obj, encoding, fake_rop):
        self._obj = obj
        self._encoding = encoding
        self._fake_rop = fake_rop

    @classmethod
    def _gen_rop_name(self, name):
        """
        gen fake rop name, just removing the first 'r' in original name
        """
        return name.replace('r', '', 1)

    @classmethod
    def _cvt_arg(self, arg):
        """
        single argument conversion, return internal obj if arg is an UObj instance
        """
        if isinstance(arg, UObj):
            return arg._obj
        return arg

    @classmethod
    def _cvt_args(self, *args):
        """
        sequence argument conversion
        """
        return [UObj._cvt_arg(a) for a in args]

    @classmethod
    def _cvt_kwargs(self, **kwargs):
        """
        keyword argument conversion
        """
        new_kwargs = {}
        for key, value in kwargs.iteritems():
            new_kwargs[UObj._cvt_arg(key)] = UObj._cvt_arg(value)
        return new_kwargs

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __cmp__(self, other):
        other = UObj._cvt_arg(other)
        if self._obj == other:
            return 0
        elif self._obj > other:
            return 1
        else:
            return -1

    def __unicode__(self):
        return to_unicode(self._obj, self._encoding)

    def __getattr__(self, name):
        fake_rop = False
        if (not hasattr(self._obj, name)) and (name in UObj.rops):
            new_name = UObj._gen_rop_name(name)
            if hasattr(self._obj, new_name):
                name = new_name
                fake_rop = True
        attr = getattr(self._obj, name)
        if name in UObj.raw_attrs:
            return attr
        return gen_uobj(attr, self._encoding, fake_rop)

    def __call__(self, *args, **kwargs):
        if self._fake_rop:
            return gen_uobj(getattr(args[0], self.__name__)(self._obj.__self__), self._encoding)
        return gen_uobj(self._obj(*(UObj._cvt_args(*args)), **(UObj._cvt_kwargs(**kwargs))),
                        self._encoding)

    def origin(self):
        return self._obj


def gen_uobj(obj, encoding="utf-8", fake_rop=False):
    """
    转成Unicode
    :param obj:
    :param encoding:
    :param fake_rop:
    :return:
    """
    if isinstance(obj, str):
        return obj.decode(encoding, 'ignore')

    if not obj or isinstance(obj, UObj.base_types):
        return obj

    return UObj(obj, encoding, fake_rop)


def html2text(html):
    html2text_handler = HTML2Text()
    html2text_handler.ignore_images = True
    html2text_handler.ignore_links = True
    text = html2text_handler.handle(to_unicode(html))
    return text


def text_filter(text):
    u'''
    过滤：
    1. 论坛
    2. 转载自：
    3. 私服
    4. 微信公众号
    5. 新浪微博
    6. 所有的链接
    '''

    text = to_unicode(text)

    words = [
        u"论坛",
        u"转载自：",
        u"私服",
        u"微信公众号",
        u"新浪微博",
        u"微博",
        u"微信号",
        u"微信",
        u"我是男的",
    ]

    for word in words:
        text = text.replace(word, "")

    # 过滤网址
    text = re.sub(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", "", text)
    text = re.sub(r"www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", "", text)
    # 过滤QQ
    text = re.sub(r"QQ[0-9]+", "", text)

    return text


def md5(content):
    return hashlib.md5(content).hexdigest()


def hash_password(password, user_id):
    return hashlib.md5("%s%s%s" % (user_id, password, user_id)).hexdigest()


def gen_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=365),
        'nbf': datetime.datetime.utcnow(),
    }

    try:
        return jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
    except Exception, e:
        logger.error(e)
        return ""


def decode_from_access_token(encoded):
    d = {}
    if encoded:
        try:
            d = jwt.decode(encoded, config.JWT_SECRET, algorithms=['HS256'])
        except Exception, e:
            logger.get("auth").error(e)
    return AttrDict(d if d else {})


def convert_underscore2camelcase(word):
    s = ''.join(x.capitalize() or '_' for x in word.split('_'))
    s = s[0].lower() + s[1:]
    return s


def convert_dict_key_underscore2camelcase(d):
    if not d:
        return d
    attr_dict = AttrDict()
    for k, v in d.iteritems():
        attr_dict[convert_underscore2camelcase(k)] = d[k]
    return attr_dict


def convert_list_underscore2camelcase(l):
    return [convert_dict_key_underscore2camelcase(i) for i in l]


def send_sms(mobile, content):
    if not config.IS_SEND_SMS:
        return True

    # TODO 优化，将发送短信放到队列里面慢慢发
    from py4j.java_gateway import JavaGateway, Py4JNetworkError

    try:
        gateway = JavaGateway(eager_load=True)
        app = gateway.entry_point
        ret = app.sendSms(mobile, content)

        logger.get("sms-log").info("send to %s, data [%s], ret: %s", mobile, content, ret)

        return ret
    except Py4JNetworkError:
        logger.get("interface-log").error("No JVM listening")
    except Exception, e:
        logger.get("interface-log").error(e)

    return False


def gen_sms_token(usage, mobile, captcha):
    s = "DJ_CAPTCHA_%s_%s_%s" % (usage, mobile, captcha)
    return md5(s)


USER_ID_BIT_OFFSET = (
    131224, 5078, 129384, 26323, 1092954, 713412, 23862, 1796, 561224, 190246,
    628253, 874, 95, 22342, 10, 829283, 302532, 47, 56, 518721,
    62, 50, 15623427, 82374827, 4710235, 2384789, 645743, 46, 312315, 2745,
    26, 37, 812, 79239482, 503, 376, 901, 28374627, 403, 204,
    12, 30, 271872361, 460, 157872732, 480, 103, 704, 747, 885,
    456, 207, 823423489, 3904828, 94172112, 229, 578, 780, 24, 494,
    193, 734, 559, 714, 937, 255, 199, 751, 156, 840,
    30, 576492, 37620, 64, 212417, 3241322, 92528, 77, 91, 49,
    726, 7512893, 5273646, 32763485, 177, 9020, 216, 682, 426, 675,
    32861763, 22, 102912, 1723620, 882977, 59, 189, 161, 41223, 154,
    2374982, 4958, 15, 2349085, 6172, 453, 6, 123847, 8603, 1234718)


def gen_user_id(username):
    if username is None or len(username.strip()) == 0:
        return 0

    user_id = 0
    length = len(username)
    offset_size = len(USER_ID_BIT_OFFSET)

    for i in xrange(length):
        offset = USER_ID_BIT_OFFSET[i % offset_size]
        user_id += ord(username[i]) * offset
    return user_id


def gen_recruitment_id(owner_id):
    return gen_user_id(str(uuid.uuid4()) + str(owner_id))


def validate_signature():
    salt = request.headers.get(const.SIGNATURE.KEY_SALT)
    signature = request.headers.get(const.SIGNATURE.KEY_SIGNATURE)
    if not salt or not signature:
        return False

    url = request.url
    parse_result = urlparse.urlparse(url)
    hostname = parse_result.hostname
    if hostname is None:
        return False

    query = parse_result.query
    body = request.data
    path = parse_result.path
    token = request.headers.get("Authorization")
    session = decode_from_access_token(token)
    uid = session.get(const.SESSION.KEY_USER_ID)

    if uid is None:
        uid = ""
    if token is None:
        token = ""

    key = salt.encode(config.encoding) + config.URL_SIGN_KEY
    string_to_sign = (
        urllib.quote(path.encode(config.encoding)) +
        request.full_path.split("?")[-1].encode(config.encoding) +
        body +
        str(uid) +
        token.encode(config.encoding))

    hash_value = hmac.new(key, string_to_sign, sha1)
    computed_signature = b64encode(hash_value.digest())
    if signature == computed_signature:
        return True
    return False


def sha1OfFile(filepath):
    sha = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            block = f.read(2 ** 10)  # Magic number: one-megabyte blocks.
            if not block:
                break
            sha.update(block)
        return sha.hexdigest()


@cache.memoize(config.cache_memorized_timeout)
def get_static_file_version(full_filename):
    filename = os.path.join(current_app.static_folder, full_filename)
    sha1 = sha1OfFile(filename)
    return sha1


def validate_referrer():
    if (request.referrer and request.referrer.startswith(request.url_root) and
            request.referrer != request.url):
        return request.referrer


def guess_source():
    system_type = request.headers.get("X-SystemType")
    app_type = request.headers.get("X-AppType")

    if system_type == 'Android':
        if app_type == 'user':
            return const.SOURCE.ANDROID_USER
        elif app_type == 'business':
            return const.SOURCE.ANDROID_BUSINESS

    if system_type == 'iOS':
        if app_type == 'business':
            return const.SOURCE.IOS_BUSINESS

    if config.SOURCE == const.SOURCE.UNDEFINED:
        logger.error(
            "guess source failed, maybe you havn't configured it [url:%s]" %
            request.url)
    return config.SOURCE


def get_weekname(dt):
    d = (u"周一", u"周二", u"周三", u"周四", u"周五", u"周六", u"周日")
    return d[dt.weekday()]
