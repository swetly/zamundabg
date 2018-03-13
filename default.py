# -*- coding: utf-8 -*-
import os, sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
from ga import ga

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon').decode('utf-8')
__language__ = __addon__.getLocalizedString
__cwd__ = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode('utf-8')
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode('utf-8')
__resource__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode('utf-8')
__icon_msg__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'zamunda.png' ) ).decode('utf-8')

sys.path.insert(0, __resource__)

def Notify (msg1, msg2):
  xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (msg1, msg2, '5000', __icon_msg__)).encode('utf-8'))

if __addon__.getSetting('firstrun') == 'true':
  Notify('Settings', 'empty')
  __addon__.openSettings()
  __addon__.setSetting('firstrun', 'false')

if __addon__.getSetting('dbg') == 'true':
  dbg = True
else:
  dbg = False

if __addon__.getSetting('bg_aud') == 'true':
  ba = 1
else:
  ba = 0

if __addon__.getSetting('bg_sub') == 'true':
  bs = 1
else:
  bs = 0

if __addon__.getSetting('xxx') == 'true':
  xxx = True
else:
  xxx = False

if not __addon__.getSetting('username'):
  Notify('User', 'empty')
if not __addon__.getSetting('password'):
  Notify('Password', 'empty')

def update(name, dat, crash=None):
  payload = {}
  payload['an'] = __scriptname__
  payload['av'] = __version__
  payload['ec'] = name
  payload['ea'] = 'zamunda'
  payload['ev'] = '1'
  payload['dl'] = urllib.quote_plus(dat.encode('utf-8'))
  ga().update(payload, crash)

import traceback
try:
  from zamunda import zamunda
  z = zamunda(
              xxx = xxx,
              base_url = __addon__.getSetting('base'),
              usr = __addon__.getSetting('username'),
              passwd = __addon__.getSetting('password'),
              baud = ba,
              bsub = bs,
              path = __profile__,
              dbg = dbg
            )
except Exception, e:
  if e.args[0] == 'LoginFail':
    Notify('LoginFail', 'Check login data')
  else:
    Notify('Module Import', 'Fail')
  traceback.print_exc()
  update('exception', e.args[0], sys.exc_info())
  raise

def index_video(page, cat, search):
  try:
    c = {}
    for c in z.page(
                    int(page),
                    cat,
                    search,
                  ):
      add_video(c)

  except Exception, e:
    if e.args[0] == 'SesionError':
      Notify(str(e.args[0]),  'Check login data and try again')
    else:
      Notify(__scriptname__, str(e.args[0]))

    traceback.print_exc()
    update('exception', '%s->%s' % (e.args[0], c.get('label', None)), sys.exc_info())
    pass

def index_cat():
  c = {}
  try:
    for c in z.index():
      add_cat(c, 'DefaultFolder.png', 'DefaultFolder.png')

  except Exception, e:
    Notify(__scriptname__, str(e.args[0]))
    traceback.print_exc()
    update('exception', '%s->%s' % (e.args[0], c.get('label', None)), sys.exc_info())
    pass

def play_video(url, name):
  #p = 'plugin://plugin.video.yatp/?action=play&torrent=%s&file_index=dialog' % (z.get_magnet(url),)
  p = 'plugin://plugin.video.quasar/play?uri=%s' % (z.get_magnet(url),)

  item = xbmcgui.ListItem(path=p)
  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
  update(name, url)

def add_cat(cat, iconimage, fanart):
  u = sys.argv[0] + '?url=' + urllib.quote_plus('ddd') + '&mode=' + str(2) + '&cat=' + urllib.quote_plus(cat['cat']) + '&search=' + urllib.quote_plus(cat['search'].encode('utf-8')) + '&page=' + urllib.quote_plus(str(cat['page']))

  liz=xbmcgui.ListItem(cat['label'], iconImage='DefaultFolder.png', thumbnailImage=iconimage)
  liz.setInfo( type='Video', infoLabels={ 'Title': cat['label']})
  liz.setProperty('fanart_image', fanart)
  return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def add_video(dat):
  if dat['path'] != 'next_page':
    u = sys.argv[0] + '?url=' + urllib.quote_plus(dat['path']) + '&mode=' + str(1) + '&cat=' + urllib.quote_plus(dat['cat']) + '&name=' + urllib.quote_plus(dat['label'].encode('utf-8')) + '&search=' + urllib.quote_plus(dat['search'].encode('utf-8')) + '&page=' +urllib.quote_plus(str(dat['page']))
    liz = xbmcgui.ListItem(dat['label'], iconImage=dat['thumbnail'], thumbnailImage=dat['thumbnail'])

    liz.setInfo(type='video', infoLabels={'Title': dat['label'], 'plot': dat['info']['plot']})
    liz.setInfo('video', { 'title': dat['label']})
    liz.setProperty('fanart_image', dat['properties']['fanart_image'])
    liz.setProperty('IsPlayable' , dat['is_playable'])
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
  else:
    add_cat(dat, 'DefaultFolder.png', 'DefaultFolder.png')

def set_viewmode():
  if __addon__.getSetting('viewset') == '':
    return
  xbmc.executebuiltin('Container.SetViewMode(%s)' % __addon__.getSetting('viewset'))

def get_params():
  param = []
  paramstring = sys.argv[2]
  if len(paramstring) >= 2:
    params = sys.argv[2]
    cleanedparams = params.replace('?', '')
    if (params[len(params) - 1] == '/'):
      params = params[0:len(params) - 2]
    pairsofparams = cleanedparams.split('&')
    param = {}
    for i in range(len(pairsofparams)):
      splitparams = {}
      splitparams = pairsofparams[i].split('=')
      if (len(splitparams)) == 2:
        param[splitparams[0]] = splitparams[1]
    return param

params = get_params()
url = None
name = None
mode = None
search = None
page = None
try:
  url = urllib.unquote_plus(params['url'])
except:
  pass
try:
  name = urllib.unquote_plus(params['name'])
except:
  pass
try:
  mode = int(params['mode'])
except:
  pass
try:
  cat = urllib.unquote_plus(params['cat']).decode('utf-8')
except:
  pass
try:
  page = urllib.unquote_plus(params['page']).decode('utf-8')
except:
  pass
try:
  search = urllib.unquote_plus(params['search']).decode('utf-8')
except:
  pass

if mode == None or url == None or len(url) < 1:
  index_cat()
elif mode == 1:
  play_video(url, name)
elif mode == 2:
  if search == '!search!':
    keyb = xbmc.Keyboard('', 'Search')
    keyb.doModal()
    search = u'!none!'
    if (keyb.isConfirmed()):
     search = keyb.getText().decode('utf-8')
  index_video(page, cat, search)

xbmcplugin.setContent(int(sys.argv[1]), 'movies')
set_viewmode()
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
