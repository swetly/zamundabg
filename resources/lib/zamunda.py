# -*- coding: utf-8 -*-

import os
import re
import urllib
import requests
from bs4 import BeautifulSoup
import simplejson as json

class zamunda():
  def __init__(
                self,
                xxx,
                base_url,
                usr,
                passwd,
                path,
                baud = 0,
                bsub = 0,
                dbg = False,
                ):
    self.__usr = usr
    self.__pass = passwd
    self.__s = requests.Session()
    self.__base_url = base_url
    self.__bsub = bsub
    self.__baud = baud
    self.__dbg = dbg
    self.__CUSTOM_TRACKERS = (
      ('tr', 'http://tracker.zamunda.net/announce.php?passkey=95b29926c5b7adab4a133cfc490ed0aa'),
      ('tr', 'http://tracker.zamunda.net/announce.php?passkey=92149dad63bdd68fedffcd44d27209dc'),
      ('tr', 'http://flashtorrents.org/announce.php'),
      ('tr', 'http://94.228.192.98/announce'),
      ('tr', 'udp://9.rarbg.com:2710/announce')
    )
    self.__categories = [
                    {'cat_ids':'5','cat_name':u'HD Movies'},
                    {'cat_ids':'31','cat_name':u'Science Movies'},
                    {'cat_ids':'28','cat_name':u'Russian Movies'},
                    {'cat_ids':'24','cat_name':u'Bg Movies'},
                    {'cat_ids':'33','cat_name':u'HD Series'},
                    {'cat_ids':'7','cat_name':u'Series'},
                    {'cat_ids':'43','cat_name':u'HD Sport'},
                    {'cat_ids':'41','cat_name':u'Sport'},
                    {'cat_ids':'35','cat_name':u'Movies x264'},
                    {'cat_ids':'19','cat_name':u'Movies XviD'},
                    # {'cat_ids':'20','cat_name':u'Movies DVD-R'},
                    # {'cat_ids':'23','cat_name':u'Clips Concerts'},
                    # {'cat_ids':'29','cat_name':u'Music DVD-R'},
                  ]

    self.__HEADERS = {
      'Host' : self.__base_url.split('//')[1],
      'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:32.0) Gecko/20100101 Firefox/32.0'
    }

    if xxx == True:
      self.__categories += [
                              {'cat_ids':'9','cat_name':u'XXX'},
                              {'cat_ids':'49','cat_name':u'HD XXX'}
                            ]

    self.__ids = [d['cat_ids'] for d in self.__categories]

    self.__s_path = os.path.join(path, '', 'sesion')
    if not os.path.exists(os.path.dirname(self.__s_path)):
      os.makedirs(os.path.dirname(self.__s_path))
    if not os.path.exists(self.__s_path):
      self.__log('Use Login')
      self.__do_login()
      with open(self.__s_path, 'wb') as f:
        json.dump(
                    requests.utils.dict_from_cookiejar(self.__s.cookies),
                    f,
                    sort_keys=True,
                    indent=True,
                    encoding='utf-8',
                  )
    else:
      self.__log('Use Sessinon')
      with open(self.__s_path, 'rb') as f:
        self.__s.cookies = requests.utils.cookiejar_from_dict(json.load(f))

  def __del__(self):
    if getattr(self, '_use_log', None):
      self.__do_logout()
    self.__log('Exit')
    self.__s.close()

  def __log(self, msg):
    if self.__dbg:
      if isinstance(msg, basestring):
        print msg.encode('utf-8')
      else:
        print str(msg)

  def __do_logout(self):
    self.__log('Logout')
    self.__s.get('%s/logout.php' % self.__base_url, headers = self.__HEADERS)

  def __do_login(self):
    r = self.__s.post('%s/takelogin.php' % self.__base_url, data={'username' : self.__usr, 'password' : self.__pass}, headers = self.__HEADERS)
    if r.status_code == requests.codes.ok and re.search(self.__usr, r.text, re.IGNORECASE):
      self.__log('Login OK')
      self._use_log = True
      return True
    else:
      self.__log('Login Error')
      raise Exception("LoginFail")

  def __info_get(self, txt):
    if txt:
      txt = re.sub(r"Tip\('|\\'|'\)", '', txt)
      ff = BeautifulSoup(txt, 'html5lib')
      return {'img': ff.find('img').get('src'),'info': re.sub( r'(?:\s+)', ' ', ff.get_text(' '))}
    else:
      return {'img': 'DefaultVideo.png', 'info': ''}

  def __claean_name(self, n):
    n_sub = [
              r'\s\[.*?\]',
              r'\s\/\s.*',
            ]
    self.__log(n)
    for _sub in n_sub:
      n = re.sub(_sub, '', n)
    self.__log(n)
    return n

  def index(self):
    yield {'label': u'Search', 'cat': '0', 'page': 0, 'search': '!search!', 'is_playable': 'False'}
    yield {'label': u'Browse latest', 'cat': '0', 'page': 0, 'search': '!none!', 'is_playable': 'False'}
    for cat in self.__categories:
      yield {'label': cat['cat_name'],'cat': cat['cat_ids'], 'page': 0, 'search': '!none!', 'is_playable': 'False'}

  def page(self, page, cat, search=None):
    fnd = {
            'search': '',
            'incldead': '0',
            'in': 'name',
          }
    fnd['page'] = page
    fnd['cat'] = cat
    fnd['bgsubs'] = self.__bsub
    fnd['bgaudio'] = self.__baud

    if search != '!none!' and search != '!search!':
      fnd['search'] =  search.encode('cp1251')
      self.__log('Search string: %s' % (search,))

    self.__log('Payload: %s' % (str(fnd),))
    r = self.__s.get('%s/bananas' % self.__base_url, params=fnd, headers = self.__HEADERS)

    if self.__dbg:
       with open(os.path.join(os.path.dirname(self.__s_path), '', 'dump.html'), 'wb') as f:
         f.write(r.text.encode('utf-8'))

    if r.status_code != requests.codes.ok:
      self.__log('Page Error')
      raise Exception("PageError")

    if not re.search(self.__usr, r.text, re.IGNORECASE):
      if os.path.exists(self.__s_path):
        os.remove(self.__s_path)
      self.__log('Sesion Error')
      raise Exception("SesionError")

    sp = BeautifulSoup(r.text, 'html5lib')
    #for link in sp.findAll('a', href=re.compile(r'\/download_go\.php\?id=\d+&m=x')):
    for link in sp.findAll('a', href=re.compile(r'\/magnetlink\/*')):
      pr = link.find_parent('td')
      if cat != '0' or pr.find_previous_sibling('td').find('a', href=re.compile(r'list\?cat=\d+'))['href'].split('=')[1] in self.__ids:
        ss = pr.find_next_siblings('td')
        dat = pr.find('a', href=re.compile(r'banan\?id=\d+'))
        r = self.__info_get(dat.get('onmouseover'))
        yield {
            'label': self.__claean_name(dat.string),
            'path': link['href'],
            'is_playable': 'True',
            'info': {'plot': '[COLOR CC00FF00]%s - DLs:%s S:%s[/COLOR][CR]%s' % (ss[3].get_text(' '), ss[4].get_text(' '), ss[5].string, r['info'],)},
            'thumbnail': r['img'],
            'cat': cat,
            'page': page,
            'search': search,
            'properties': {'fanart_image': r['img']}
        }
    nn = sp.find('b', text=re.compile(u'(?:Следваща.)'))
    if nn and nn.find_parent('a'):
      yield {
          'label': '>> Next page',
          'path': 'next_page',
          'cat': cat,
          'page': page+1,
          'is_playable': 'False',
          'search': search,
      }

  def get_magnet(self, p):
    r = self.__s.get('%s%s' % (self.__base_url, p), headers = self.__HEADERS)
    s = re.search(r"^.*?href='(magnet.*)'", r.text, re.M|re.I)
    if s:
      return'%s&%s' % (s.group(1), urllib.urlencode(self.__CUSTOM_TRACKERS),)
