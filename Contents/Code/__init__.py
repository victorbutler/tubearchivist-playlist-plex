#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, hashlib, re, inspect, json, sys
import datetime
import json
import ssl
import inspect
import urllib2
from io import open
from lxml import etree
try:
  from ssl import PROTOCOL_TLS as SSL_PROTOCOL # Python >= 2.7.13 #ssl.PROTOCOL_TLSv1
except ImportError:  
  from ssl import PROTOCOL_SSLv23 as SSL_PROTOCOL # Python <  2.7.13
try:
  from urllib.request import urlopen, Request     # Python >= 3.0
except ImportError:
  from urllib2 import urlopen, Request     # Python == 2.x
try:
  from urllib.parse import quote
except:
  from urllib import quote

# import inspect

TA_CONFIG              = {}
PLUGIN_PATH            = os.path.abspath(os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "..", ".."))

PLEX_ROOT              = os.path.abspath(os.path.join(PLUGIN_PATH, "..", ".."))
CachePath              = os.path.join(PLEX_ROOT, "Plug-in Support", "Data", "com.plexapp.agents.tubearchivist-agent", "DataItems")
PLEX_LIBRARY           = {}
PLEX_LIBRARY_URL       = "http://localhost:32400/library/sections/"  # Allow to get the library name to get a log per library https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token
SOURCE                 = "TubeArchivist Agent"
CON_AGENTS             = ['com.plexapp.agents.none']
REF_AGENTS             = ['com.plexapp.agents.localmedia']
LANGUAGES              = [Locale.Language.NoLanguage, Locale.Language.English]

SSL_CONTEXT            = ssl.SSLContext(SSL_PROTOCOL)
FILTER_CHARS    = "\\/:*?<>|;"
youtube_regexs = [
  '[0-9]{8}_[a-zA-Z0-9]{11}_*.*',    # YYYYMMDD_XXXXXXXXXXX_TITLE.ext | Legacy TA title
  '[a-zA-Z0-9]{11}.*',               # XXXXXXXXXXX.ext                | v0.4.0+
]

YOUTUBE_CATEGORY_ID      = {  '1': 'Film & Animation',  '2': 'Autos & Vehicles',  '10': 'Music',          '15': 'Pets & Animals',        '17': 'Sports',                 '18': 'Short Movies',
                             '19': 'Travel & Events',  '20': 'Gaming',            '21': 'Videoblogging',  '22': 'People & Blogs',        '23': 'Comedy',                 '24': 'Entertainment',
                             '25': 'News & Politics',  '26': 'Howto & Style',     '27': 'Education',      '28': 'Science & Technology',  '29': 'Nonprofits & Activism',  '30': 'Movies',
                             '31': 'Anime/Animation',  '32': 'Action/Adventure',  '33': 'Classics',       '34': 'Comedy',                '35': 'Documentary',            '36': 'Drama', 
                             '37': 'Family',           '38': 'Foreign',           '39': 'Horror',         '40': 'Sci-Fi/Fantasy',        '41': 'Thriller',               '42': 'Shorts',
                             '43': 'Shows',            '44': 'Trailers'}


###Mini Functions ###
def natural_sort_key     (s):  return [int(text) if text.isdigit() else text for text in re.split(re.compile('([0-9]+)'), str(s).lower())]  ### Avoid 1, 10, 2, 20... #Usage: list.sort(key=natural_sort_key), sorted(list, key=natural_sort_key)
def sanitize_path        (p):  return p if isinstance(p, unicode) else p.decode(sys.getfilesystemencoding()) ### Make sure the path is unicode, if it is not, decode using OS filesystem's encoding ###
#####################


# def DebugObject (obj):
#   output = ""
#   output = "{}\n\t{}".format(output, str(obj))
#   for attr in inspect.getmembers(obj):
#     if not attr[0].startswith("__"):
#       output = "{}\n\t{}".format(output, str(attr))
#   return output


def Dict(var, *arg, **kwarg):  #Avoid TypeError: argument of type 'NoneType' is not iterable
  for key in arg:
    if isinstance(var, dict) and key and key in var or isinstance(var, list) and isinstance(key, int) and 0<=key<len(var):
      var = var[key]
    else:
      return kwarg['default'] if kwarg and 'default' in kwarg else ""   # Allow Dict(var, tvdbid).isdigit() for example
  return kwarg['default'] if var in (None, '', 'N/A', 'null') and kwarg and 'default' in kwarg else "" if var in (None, '', 'N/A', 'null') else var


def GetMediaDir (media, movie=False, file=False):
  if movie:
    return os.path.dirname(media.items[0].parts[0].file)
  else:
    for s in media.seasons if media else []: # TV_Show:
      for e in media.seasons[s].episodes:
        return media.seasons[s].episodes[e].items[0].parts[0].file if file else os.path.dirname(media.seasons[s].episodes[e].items[0].parts[0].file)
      

def read_url(url, data=None):
  url_content = ""
  try:
    if data is None:
      url_content = urlopen(url, context=SSL_CONTEXT).read()
    else:
      url_content = urlopen(url, context=SSL_CONTEXT, data=data).read()
    return url_content
  except Exception as e:
    Log.Error("Error reading or accessing url '%s', Exception: '%s'" % (url, e))
    raise e
  

def read_file(localfile):
  file_content = ""
  try:
    with open(localfile, 'r') as file:  file_content = file.read()
    return file_content
  except Exception as e:
    Log.Error("Error reading or accessing file '%s', Exception: '%s'" % (localfile, e))
    raise e

      
### Plex Library XML ###
# token_file_path = os.path.join(PLEX_ROOT, "X-Plex-Token.id")
# if os.path.isfile(token_file_path):
#   Log.Info(u"'X-Plex-Token.id' file present")
#   token_file=Data.Load(token_file_path)
#   if token_file:  PLEX_LIBRARY_URL += "?X-Plex-Token=" + token_file.strip()
#   #Log.Info(PLEX_LIBRARY_URL) ## Security risk if posting logs with token displayed
# try:
#   library_xml = etree.fromstring(urllib2.urlopen(PLEX_LIBRARY_URL).read())
#   for library in library_xml.iterchildren('Directory'):
#     for path in library.iterchildren('Location'):
#       PLEX_LIBRARY[path.get("path")] = library.get("title")
# except Exception as e:
#   Log.Info(u"Place correct Plex token in {} file to have a log per library - https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token, Error: {}".format(token_file_path, str(e)))


def load_ta_config():
  global TA_CONFIG
  if TA_CONFIG:
    TA_CONFIG['online'], TA_CONFIG['version'] = test_ta_connection()
    return
  else:
    Log.Info("Loading TubeArchivist configurations from Plex Agent configuration.")
    if Prefs['tubearchivist_url']:
      TA_CONFIG['ta_url'] = Prefs['tubearchivist_url']
    if Prefs['tubearchivist_api_key']:
      TA_CONFIG['ta_api_key'] = Prefs['tubearchivist_api_key']
    TA_CONFIG.update(get_ta_config())
    TA_CONFIG['online'] = False
    TA_CONFIG['version'] = [0,0,0]
    TA_CONFIG['online'], TA_CONFIG['version'] = test_ta_connection()


def get_ta_config():
  AGENT_LOCATION = os.path.join(PLUGIN_PATH, "Contents")
  CONFIG_NAME = "config.json"
  Log.Info("Checking if there are any overriding configurations in a local file...")
  return json.loads(read_file(os.path.join(AGENT_LOCATION, CONFIG_NAME)) if os.path.isfile(os.path.join(AGENT_LOCATION, CONFIG_NAME)) else "{}")


def test_ta_connection():
  if not TA_CONFIG:
    return
  try:
    Log.Info("Attempting to connect to TubeArchivist at {} with provided token from `ta_config.json` file to test connection and poll version details.".format(TA_CONFIG['ta_url']))
    response = json.loads(read_url(Request("{}/api/ping".format(TA_CONFIG['ta_url']), headers={"Authorization": "Token {}".format(TA_CONFIG['ta_api_key'])})))
    ta_ping = response['response']
    ta_version = []
    try:
      if "version" in response:
        ta_version = response['version']
        Log.Info("TubeArchivist is running version v{}".format('.'.join(str(x) for x in ta_version)))
      else:
        ta_version = [0,3,6]
        Log.Info("TubeArchivist did not respond with a version. Assuming v{} for interpretation.".format('.'.join(str(x) for x in ta_version)))
    except:
      Log.Error("Unable to set the `ta_version`. Check the connection via `ta_ping`.")
    if ta_ping == 'pong':
      return True, ta_version
  except Exception as e:
    Log.Error("Error connecting to TubeArchivist with URL '%s', Exception: '%s'" % (TA_CONFIG['ta_url'], e))
    raise e


def get_ta_metadata(id, mtype="video"):
  request_url = ""
  request_url = "{}/api/{}/{}/".format(TA_CONFIG['ta_url'], mtype, id)
  if not TA_CONFIG:
    return
  try:
    Log.Info("Attempting to connect to TubeArchivist to lookup YouTube {}: {}".format(mtype, id))
    response = json.loads(read_url(Request(request_url, headers={"Authorization": "Token {}".format(TA_CONFIG['ta_api_key'])})))
    return response
  except Exception as e:
    Log.Error("Error connecting to TubeArchivist with URL '{}', Exception: '{}'".format(request_url, e))
    raise e


def get_ta_video_metadata(ytid):
  mtype = "video"
  if not TA_CONFIG:
    Log.Error("No configurations in TA_CONFIG.")
    return
  if not ytid:
    Log.Error("No {} ID present.".format(mtype))
    return
  try:
    vid_response = get_ta_metadata(ytid)
    Log.Info("Response from TubeArchivist received for YouTube {}: {}".format(mtype, ytid))
    if vid_response:
      metadata = {}
      if Prefs['show_channel_id']:
        metadata['show'] = "{} [{}]".format(vid_response['data']['channel']['channel_name'], vid_response['data']['channel']['channel_id'])
      else:
        metadata['show'] = "{}".format(vid_response['data']['channel']['channel_name'])
      metadata['ytid'] = vid_response['data']['youtube_id']
      metadata['title'] = vid_response['data']['title']
      metadata['processed_date'] = Datetime.ParseDate(vid_response['data']['published'])
      video_refresh = Datetime.ParseDate(vid_response['data']['vid_last_refresh'])
      metadata['refresh_date'] = video_refresh.strftime("%Y%m%d")
      
      metadata['season'] = metadata['processed_date'].year
      metadata['episode'] = metadata['processed_date'].strftime("%Y%m%d")
      if len(vid_response['data']['playlist']) > 0:
        playlist_response = get_ta_metadata(vid_response['data']['playlist'][0])
        if playlist_response:
          metadata['season'] = playlist_response['data']['playlist_name']
          filtered_arr = [p for p in playlist_response['data']['playlist_entries'] if p.youtube_id == ytid]
          metadata['episode'] = filtered_arr[0]['idx'] + 1

      metadata['description'] = vid_response['data']['description']
      metadata['thumb_url'] = vid_response['data']['vid_thumb_url']
      metadata['type'] = vid_response['data']['vid_type']
      metadata['has_subtitles'] = True if 'subtitles' in vid_response['data'] else False
      if metadata['has_subtitles']:
        metadata['subtitle_metadata'] = vid_response['data']['subtitles']
      return metadata
    else:
      Log.Error("Empty response returned from %s when requesting data about %s." % (TA_CONFIG['ta_url'], mtype))
  except Exception as e:
    Log.Error("Error processing %s response from TubeArchivist at URL '%s', Exception: '%s'" % (mtype, TA_CONFIG['ta_url'], e))
    raise e


def get_ta_channel_metadata(chid):
  mtype = "channel"
  if not TA_CONFIG:
    Log.Error("No configurations in TA_CONFIG.")
    return
  if not chid:
    Log.Error("No {} ID present.".format(mtype))
    return
  try:
    ch_response = get_ta_metadata(chid, mtype="channel")
    Log.Info("Response from TubeArchivist received for YouTube {}: {}".format(mtype, chid))
    if ch_response:
      metadata = {}
      if Prefs['show_channel_id']:
        metadata['show'] = "{} [{}]".format(ch_response['data']['channel_name'], ch_response['data']['channel_id'])
      else:
        metadata['show'] = "{}".format(ch_response['data']['channel_name'])
      channel_refresh = Datetime.ParseDate(ch_response['data']['channel_last_refresh'])
      metadata['refresh_date'] = channel_refresh.strftime("%Y%m%d")
      metadata['description'] = "YouTube ID: {}\n\n{}".format(ch_response['data']['channel_id'], ch_response['data']['channel_description'])
      metadata['banner_url'] = ch_response['data']['channel_banner_url']
      metadata['thumb_url'] = ch_response['data']['channel_thumb_url']
      metadata['tvart_url'] = ch_response['data']['channel_tvart_url']
      return metadata
    else:
      Log.Error("Empty response returned from %s when requesting data about %s." % (TA_CONFIG['ta_url'], mtype))
  except Exception as e:
    Log.Error("Error processing %s response from TubeArchivist at URL '%s', Exception: '%s'" % (mtype, TA_CONFIG['ta_url'], e))
    raise e


def PullTASubtitles(vid_metadata, filepath, media_obj):
  lang_sub_map      = {}
  lang_pub_map      = []
  languages         = {}
  language_index    = 0

  for sub in vid_metadata['subtitle_metadata']:
    codec       = ''
    format      = ''
    forced      = ''
    default     = ''
    (_, ext)    = os.path.splitext(sub['media_url'])

    if ext in ['.vtt']:
      codec         = 'vtt'
      format        = None
      lang_match    = Locale.Language.Match(sub['lang'])

      if os.path.exists(filepath):
        filename        = os.path.basename(sub['media_url'])
        plex_sub_path   = os.path.join(filepath, filename)

        if os.path.exists(plex_sub_path):
          if not languages.has_key(lang_match):
            languages[lang_match]     = []
          if "Default" in sub['name']:
            default                   = '1'
          if "Forced" in sub['name'] or "user" in sub['source']:
            forced                    = '1'
          additional_classifications  = []
          if default:
            additional_classifications.append("Default")
          if forced:
            additional_classifications.append("Forced")
          if not additional_classifications:
            additional_classifications.append("None")
          Log.Info("Locally downloaded subtitle identified for video ID {} with language code '{}'. Additional classifications: {}".format(vid_metadata['ytid'], lang_match, ", ".join(additional_classifications)))

          for item in media_obj.items:
            for part in item.parts:
              part.subtitles[lang_match][filename] = Proxy.LocalFile(plex_sub_path, codec=codec, format=format, default=default, forced=forced)
          language_index              += 1

          if lang_match not in lang_sub_map:
            lang_sub_map[lang_match] = []
          lang_sub_map[lang_match].append(filename)

        else:
          Log.Error("Cannot find subtitle locally. Subtitle does not exist with video's path replacement '{}'.".format(plex_sub_path))
      else:
        Log.Error("Cannot find subtitle locally. Video's path of '{}' does not exist or is inaccessible.".format(filepath))
  
  for lang, subtitle in lang_sub_map.items():
    if subtitle not in lang_pub_map:
      lang_pub_map.append(subtitle[0])

  # for lang in languages.keys():
  #   for item in media_obj.items:
  #     for part in item.parts:
  #       for filename in lang_sub_map[lang]:
  #         part.subtitles[lang][filename] = languages[lang]

  for item in media_obj.items:
    for part in item.parts:
      # Log.Debug("Validating keys for {}.".format(lang_pub_map))
      # Log.Debug("Output part details: \nPART: {}\nSUBTITLES: {}\n".format(DebugObject(part),DebugObject(part.subtitles)))
      # for language in part.subtitles.keys():
      #   Log.Debug("\nLANG({}): {}".format(language, DebugObject(part.subtitles[language])))
      for language in lang_sub_map.keys():
        part.subtitles[language].validate_keys(lang_pub_map)
      for language in list(set(part.subtitles.keys()) - set(lang_sub_map.keys())):
        Log.Info("Removing language code '{}' that is no longer available as a locally downloaded subtitle for video ID {}.".format(language, vid_metadata['ytid']))
        part.subtitles[language].validate_keys({})

  # for item in media_obj.items:
  #   for part in item.parts:
  #     for language in part.subtitles.keys():
  #       Log.Debug("Output part details: \nPART: {}\nSUBTITLES: {}\n".format(DebugObject(part),DebugObject(part.subtitles)))
  #       for language in part.subtitles.keys():
  #         Log.Debug("\nLANG({}): {}".format(language, DebugObject(part.subtitles[language])))

def GetLibraryRootPath(dir):
  library, root, path = '', '', ''
  for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(0, dir.count(os.sep))]:
    if root in PLEX_LIBRARY:
      library = PLEX_LIBRARY[root]
      path    = os.path.relpath(dir, root)
      break
  else:  #401 no right to list libraries (windows)
    Log.Info(u'[X] Library access denied')
    filename = os.path.join(CachePath, '_Logs', '_root_.scanner.log')
    if os.path.isfile(filename):
      Log.Info(u'[_] TubeArchivist Playlist root scanner log file present: "{}"'.format(filename))
      line = Core.storage.load(filename)  #with open(filename, 'rb') as file:  line=file.read()
      for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(dir.count(os.sep)-1, -1, -1)]:
        if "root: '{}'".format(root) in line:  path = os.path.relpath(dir, root).rstrip('.');  break  #Log.Info(u'[!] root not found: "{}"'.format(root))
      else: path, root = '_unknown_folder', ''
    else:  Log.Info(u'[!] TubeArchivist Playlist root scanner log file missing: "{}"'.format(filename))
  return library, root, path


def Search(results, media, lang, manual):
  displayname   = sanitize_path(os.path.basename(media.show))
  filename      = media.filename or media.show
  dir           = GetMediaDir(media)

  try:
    filename = sanitize_path(filename)
  except Exception as e:
    Log.Error("Failure to sanitize filename: '{}', Exception: '{}'".format(filename, e))
  try:
    filename = os.path.basename(filename)
  except Exception as e:
    Log.Error("Failure to get basename of filename: '{}', Exception: '{}'".format(filename, e))
  try:
    filename = urllib2.unquote(filename)
  except Exception as e:
    Log.Error("Failure to remove invalid characters in filename: '{}', Exception: '{}'".format(filename, e))
  try:
    if (displayname.rindex('[') > 0) and (displayname.rindex(']') > 0 and displayname.rindex(']') > displayname.rindex('[')):
      guid = displayname[(displayname.rindex('[') + 1):(displayname.rindex(']'))]
      results.Append(MetadataSearchResult(id='tubearchivist|{}|{}'.format(guid,os.path.basename(dir)), name=displayname, year=media.year, score=100, lang=lang))
      Log.Info("TubeArchivist ID was found - Display Name: {} | File: {}".format(displayname, filename))
      return
    else:
      Log.Error("TubeArchivist ID not found - Display Name: {} | File: {}".format(displayname, filename))
  except Exception as e:
    Log.Error('Search for file with filename: "{}" - Failed to find and process TubeArchivist ID, Exception: "{}"'.format(filename, e))
  library, root, path = GetLibraryRootPath(dir)
  results.Append(MetadataSearchResult(id='tubearchivist|{}|{}'.format(path.split(os.sep)[-2] if os.sep in path else '', dir), name=os.path.basename(filename), year=None, score=80, lang=lang))
  return 1


def Update(metadata, media, lang, force):
  _, guid, series_folder    = metadata.id.split("|")
  channel_id                = guid
  channel_title             = ""
  ch_metadata               = {}

  if TA_CONFIG['online']:
    ch_metadata             = get_ta_channel_metadata(channel_id)
    channel_title           = ch_metadata['show']
  else:
    channel_title           = metadata.title

  metadata.title            = channel_title

  if TA_CONFIG['online']:
    thumb_channel = "{}_{}".format(ch_metadata['refresh_date'], ch_metadata['thumb_url'])
    if thumb_channel and thumb_channel not in metadata.posters:
      metadata.posters[thumb_channel] = Proxy.Media(read_url(Request("{}{}".format(TA_CONFIG['ta_url'],ch_metadata['thumb_url']), headers={"Authorization": "Token {}".format(TA_CONFIG['ta_api_key'])})), sort_order=1 if Prefs['media_poster_source'] == "Channel" else 2)
      Log(u'[X] Posters: {}'.format(thumb_channel))
    elif thumb_channel and thumb_channel in metadata.posters:
      Log(u'[_] Posters: {}'.format(thumb_channel))
    else:
      Log(u'[ ] Posters: {}'.format(thumb_channel))

    tvart_channel = "{}_{}".format(ch_metadata['refresh_date'], ch_metadata['tvart_url'])
    if tvart_channel and tvart_channel not in metadata.art:
      metadata.art[tvart_channel] = Proxy.Media(read_url(Request("{}{}".format(TA_CONFIG['ta_url'],ch_metadata['tvart_url']), headers={"Authorization": "Token {}".format(TA_CONFIG['ta_api_key'])})), sort_order=1 if Prefs['media_poster_source'] == "Channel" else 2)
      Log(u'[X] Art: {}'.format(tvart_channel))
    elif tvart_channel and tvart_channel in metadata.art:
      Log(u'[_] Art: {}'.format(tvart_channel))
    else:
      Log(u'[ ] Art: {}'.format(tvart_channel))

    banner_channel = "{}_{}".format(ch_metadata['refresh_date'], ch_metadata['banner_url'])
    if banner_channel and banner_channel not in metadata.banners:
      metadata.banners[banner_channel] = Proxy.Media(read_url(Request("{}{}".format(TA_CONFIG['ta_url'],ch_metadata['banner_url']), headers={"Authorization": "Token {}".format(TA_CONFIG['ta_api_key'])})), sort_order=1 if Prefs['media_poster_source'] == "Channel" else 2)
      Log(u'[X] Banners: {}'.format(banner_channel))
    elif banner_channel and banner_channel in metadata.banners:
      Log(u'[_] Banners: {}'.format(banner_channel))
    else:
      Log(u'[ ] Banners: {}'.format(banner_channel))

    metadata.roles.clear()
    role                = metadata.roles.new()
    role.role           = channel_title
    role.name           = channel_title
    role.photo          = thumb_channel

    metadata.summary    = ch_metadata['description']
    metadata.studio     = "YouTube"

    Log.Info("Channel metadata updates completed for {}.".format(channel_title))

    episodes            = 0

    for s in sorted(media.seasons, key=natural_sort_key):
      for e in sorted(media.seasons[s].episodes, key=natural_sort_key):
        episode                         = metadata.seasons[s].episodes[e]
        episodes                       += 1
        episode_media                   = media.seasons[s].episodes[e]
        episode_part                    = episode_media.items[0].parts[0]
        filename                        = os.path.basename(episode_part.file)
        filepath                        = os.path.dirname(episode_part.file)
        filename_noext, filename_ext    = os.path.splitext(filename)
        episode_id                      = ""
        if TA_CONFIG['version'] > [0,3,6] and TA_CONFIG['online']:
          episode_id                    = filename_noext
        elif TA_CONFIG['online']: # Assume that if it is online and less that v0.4.0, it is compatible with the legacy file name schema
          episode_id                    = filename[9:20]

        if TA_CONFIG['online']:
          vid_metadata                      = get_ta_video_metadata(episode_id)
          episode.title                     = vid_metadata['title']
          episode.summary                   = "YouTube ID: {}{}\n{}".format(episode_id,"\nVideo Type: {}".format(vid_metadata['type']) if "video" not in vid_metadata['type'] else "",vid_metadata['description'])
          episode.originally_available_at   = vid_metadata['processed_date'].date()

          thumb_vid = "{}_{}".format(vid_metadata['refresh_date'], vid_metadata['thumb_url'])
          if thumb_vid and thumb_vid not in episode.thumbs:
            episode.thumbs[thumb_vid] = Proxy.Media(read_url(Request("{}{}".format(TA_CONFIG['ta_url'],vid_metadata['thumb_url']), headers={"Authorization": "Token {}".format(TA_CONFIG['ta_api_key'])})), sort_order=1 if Prefs['media_poster_source'] == "Channel" else 2)
            Log(u'[X] Thumbs: {}'.format(thumb_vid))
          elif thumb_vid and thumb_vid in episode.thumbs:
            Log(u'[_] Thumbs: {}'.format(thumb_vid))
          else:
            Log(u'[ ] Thumbs: {}'.format(thumb_vid))
        
          if vid_metadata['has_subtitles']:
            PullTASubtitles(vid_metadata, filepath, episode_media)
          else:
            Log.Info("No downloaded subtitles associated with video ID {}. No request made to TubeArchivist.".format(episode_id))
          Log.Info("Episode '{} - {}' for channel {} processed successfully.".format(episode_id, episode.title, channel_title))
    Log.Info("All episode files processed for {}. Count: {}".format(channel_title, str(episodes)))
    Log.Info("=== End Of Agent's Update Call, errors after this are Plex related ===")


class TubeArchivistYTSeriesAgent(Agent.TV_Shows):
    name, primary_provider, fallback_agent, contributes_to, accepts_from, languages = (
      SOURCE, True, False, CON_AGENTS, REF_AGENTS, LANGUAGES)

    def search(self, results,  media, lang, manual):
        load_ta_config()
        Search(results,  media, lang, manual)
    

    def update(self, metadata, media, lang, force):
        load_ta_config()
        Update(metadata, media, lang, force)


def Start():
    #HTTP.CacheTime                  = CACHE_1MONTH
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36' # Generisize further
    HTTP.Headers['Accept-Language'] = 'en-us'
    Log("Starting up TubeArchivist Playlist Agent...")