import os
import sys
import time
import base64

import json
import requests
from requests_oauthlib import OAuth1


MEDIA_ENDPOINT_URL = 'https://upload.twitter.com/1.1/media/upload.json'
POST_TWEET_URL = 'https://api.twitter.com/1.1/statuses/update.json'

CONSUMER_KEY = 'your-consumer-key'
CONSUMER_SECRET = 'your-consumer-secret'
ACCESS_TOKEN = 'your-access-token'
ACCESS_TOKEN_SECRET = 'your-access-secret'

VIDEO_FILENAME = 'icon.jpg'


oauth = OAuth1(CONSUMER_KEY,
  client_secret=CONSUMER_SECRET,
  resource_owner_key=ACCESS_TOKEN,
  resource_owner_secret=ACCESS_TOKEN_SECRET)


class VideoTweet(object):

  def __init__(self, file_name):
    '''
    Defines video tweet properties
    '''
    self.video_filename = file_name
    self.total_bytes = os.path.getsize(self.video_filename)
    self.media_id = None
    self.processing_info = None


  def upload_init(self):
    '''
    Initializes Upload
    '''
    print('INIT')

    request_data = {
      'command': 'INIT',
      'media_type': 'image/jpg',
      'total_bytes': self.total_bytes,
      'media_category': 'tweetimage'
    }

    req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, auth=oauth)
    media_id = req.json()['media_id']

    self.media_id = media_id

    print('Media ID: %s' % str(media_id))


  def upload_append(self):
    '''
    Uploads media in chunks and appends to chunks uploaded
    '''
    segment_id = 0
    characters_sent = 0

    with open(self.video_filename, 'rb') as fp:
      file_base64 = base64.b64encode(fp.read())

    chunk_size = len(file_base64) // 2

    while characters_sent < len(file_base64):

      chunk = file_base64[characters_sent:characters_sent+chunk_size]

      print('APPEND')

      request_data = {
        'command': 'APPEND',
        'media_id': self.media_id,
        'segment_index': segment_id
      }

      files = {
        'media_data':chunk
      }

      req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, files=files, auth=oauth)

      if req.status_code < 200 or req.status_code > 299:
        print(req.status_code)
        print(req.text)
        sys.exit(0)

      segment_id = segment_id + 1
      characters_sent = characters_sent + chunk_size

      print('%s of %s characters uploaded' % (str(characters_sent), str(len(file_base64))))

    print('Upload chunks complete.')


  def upload_finalize(self):
    '''
    Finalizes uploads and starts video processing
    '''
    print('FINALIZE')

    request_data = {
      'command': 'FINALIZE',
      'media_id': self.media_id
    }

    req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data, auth=oauth)
    print(req.json())

    self.processing_info = req.json().get('processing_info', None)
    self.check_status()


  def check_status(self):
    '''
    Checks video processing status
    '''
    if self.processing_info is None:
      return

    state = self.processing_info['state']

    print('Media processing status is %s ' % state)

    if state == u'succeeded':
      return

    if state == u'failed':
      sys.exit(0)

    check_after_secs = self.processing_info['check_after_secs']

    print('Checking after %s seconds' % str(check_after_secs))
    time.sleep(check_after_secs)

    print('STATUS')

    request_params = {
      'command': 'STATUS',
      'media_id': self.media_id
    }

    req = requests.get(url=MEDIA_ENDPOINT_URL, params=request_params, auth=oauth)

    self.processing_info = req.json().get('processing_info', None)
    self.check_status()


  def tweet(self):
    '''
    Publishes Tweet with attached video
    '''
    request_data = {
      'status': 'I just uploaded a video with the @TwitterAPI.',
      'media_ids': self.media_id
    }

    req = requests.post(url=POST_TWEET_URL, data=request_data, auth=oauth)
    print(req.json())


if __name__ == '__main__':
  videoTweet = VideoTweet(VIDEO_FILENAME)
  videoTweet.upload_init()
  videoTweet.upload_append()
  videoTweet.upload_finalize()
  videoTweet.tweet()
