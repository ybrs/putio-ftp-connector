#!/usr/bin/env python
# $Id: basic_ftpd.py 569 2009-04-04 00:17:43Z billiejoex $

"""A basic FTP server which uses a DummyAuthorizer for managing 'virtual
users', setting a limit for incoming connections.
"""

import os
import re
import requests

#from pyftpdlib
import ftpserver
import urllib2
import base64

import putio
from pathtoid import PathToId
import pathtoid
import config
import time
import putio2

class HttpFD(object):

    def __init__(self, apifile, bucket, obj, mode):
        self.apifile = apifile
        self.download_url = apifile.get_stream_url()
        self.bucket = bucket
        self.name = obj
        self.mode = mode
        self.closed = False
        self.total_size = None
        self.seekpos = None

        self.read_size = 0
        # speed...
        self.read_bytes = 128 * 1024 # 128kb per iteration
        self.buffer = ''
        self.req = None
        self.fd = None
        
        # gets total size
        req = urllib2.Request(self.download_url)
        f = urllib2.urlopen(req)
        self.total_size = f.headers.get('Content-Length')


    def write(self, data):
        raise OSError(1, 'Operation not permitted')
        # self.temp_file.write(data)

    def close(self):
        return

    def __read(self, size=65536):
        c =  self.buffer
        self.buffer = ''
        return c

    def read(self, size=65536):
        if self.req == None:
            self.req = urllib2.Request(self.download_url)

        if self.seekpos:
            self.req.headers['Range'] = 'bytes=%s-' % (self.seekpos)

        if self.read_size > self.total_size:
          return

        self.read_size = self.read_size + self.read_bytes + 1
        if not self.fd:
            self.fd = urllib2.urlopen(self.req)

        return self.fd.read(1024)


    def seek(self, frombytes, **kwargs):
        self.seekpos = frombytes
        return 
        

# ....
idfinder = PathToId()
idfinder.load_items()

api = None


class HttpFS(ftpserver.AbstractedFS):

    def __init__(self, cmd_channel):
        self.root = None
        self.cwd = '/'
        self.rnfr = None
        self.dirlistcache = {}
        self.idfinder = idfinder
        self.cmd_channel = cmd_channel        

    def open(self, filename, mode):
        print "filename: ", filename

        if filename in self.dirlistcache:
          apifile = self.dirlistcache[filename]
        else:
          if filename == os.path.sep:
            # items = operations.api.get_items()
            # this is not a file its a directory
            # raise OSError(1, 'This is a directory')
            raise IOError(1, 'This is a directory')
          else:
            id = idfinder.find_item_by_path(filename)
            print "file id:", filename, id
            apifile = operations.api.get_items(id=id)[0]

        if apifile.is_dir:
          raise IOError(1, 'This is a directory')

        #
        return HttpFD(apifile, None, filename, mode)

    def chdir(self, path):
        self.cwd = path.decode('utf-8').encode('utf-8')

    def mkdir(self, path):
        dirs = os.path.split(path)
        apifile = self._getitem(dirs[0])
        if not apifile: #this is root
            operations.api.create_folder(name = dirs[1], parent_id = 0)
        else:
            apifile.create_folder(name=dirs[1])
        self.remove_from_cache(path)
        self.remove_from_cache(dirs[0])
      
    def get_putio_api_client(self):        
        try:
            userdict = self.cmd_channel.authorizer.users[self.cmd_channel.username]
            if 'client' in userdict:
                return userdict['client']
            else:
                print ">>>> token:", userdict['token']
                userdict['client'] = putio2.Client(userdict['token'])
                return userdict['client']
                 
        except:
            # TODO: properly close the channel        
            raise 
    
    def listdir(self, path):
        ret = []
        try:
            item = self._getitem(path)
        except:
            return []

        if not item:
            items = self.get_putio_api_client().File.list()
        else:
            try:
                items = operations.api.get_items(parent_id=item.id)
            except:
                return []            
        for i in items:
            ret.append(i.name)          
        return ret

    def remove_from_cache(self, path):
        if path in self.dirlistcache:
            del self.dirlistcache[path]
        idfinder.invalidate_items_cache_by_path(path)

    def rmdir(self, path):
        apifile = self._getitem(path)
        if not apifile:
            raise OSError(2, 'No such file or directory')
        apifile.delete_item()
        self.remove_from_cache(path)


    def remove(self, path):
        apifile = self._getitem(path)
        if not apifile:
            raise OSError(2, 'No such file or directory')
        apifile.delete_item()
        self.remove_from_cache(path)

    def rename(self, src, dst):
      apifile = self._getitem(src)
      if not apifile:
        raise OSError(2, 'No such file or directory')

      srcs = os.path.split(src)
      dsts = os.path.split(dst)

      if srcs[0] != dsts[0]:
        # this is a move operation..
        if dsts[0] == os.path.sep:
          apifile.move_item(target=0)
          return
          
        destination = self._getitem(dsts[0]);
        if not destination:
          raise OSError(2, 'No such file or directory')
        apifile.move_item(target=destination.id)
        return

      apifile.rename_item(dsts[1])
      self.remove_from_cache(src)
      self.remove_from_cache(srcs[0])
      self.remove_from_cache(dst)
      self.remove_from_cache(dsts[0])

    def isfile(self, path):
        return not self.isdir(path)

    def islink(self, path):
        return False

    def isdir(self, path):
        if path == os.path.sep:
            return True
        apifile = self._getitem(path)
        if not apifile:
            raise OSError(2, 'No such file or directory')
        if apifile.is_dir:
            return True
        else:
            return False

    def getsize(self, path):
        apifile = self._getitem(path)
        if not apifile:
            raise OSError(1, 'No such file or directory')
        print "filesize :", apifile.size
        return long(apifile.size)
        #return self.stat(path).st_size

    def getmtime(self, path):
        return self.stat(path).st_mtime

    def realpath(self, path):
        return path

    def lexists(self, path):
        apifile = self._getitem(path)
        if not apifile:
            raise OSError(2, 'No such file or directory')
        return apifile

    def _getitem(self, filename):
        if filename in self.dirlistcache:
          apifile = self.dirlistcache[filename]
          print 'found........', apifile.id, apifile.name
        else:
          if filename == os.path.sep:
            # items = operations.api.get_items()
            return False
          else:
            id = idfinder.find_item_by_path(filename)
            print "file id:", id
            apifile = operations.api.get_items(id=id)[0]
            self.dirlistcache[filename] = apifile
            
        return apifile #.get_download_url()


    def stat(self, path):
        apifile = self._getitem(path)
        return os.stat_result((666, 0L, 0L, 0, 0, 0, apifile.size, 0, 0, 0))

    exists = lexists
    lstat = stat

    def validpath(self, path):
        return True

    def format_list_items(self, items):
        for item in items:
            if item.is_dir:
                s = 'drwxrwxrwx 1 %s group %8s Jan 01 00:00 %s\r\n' % ('aaa', 0, item.name)
            else:
                s = '-rw-rw-rw- 1 %s group %8s %s %s\r\n' % ('aaa', item.size, time.strftime("%b %d %H:%M"), item.name)
            yield s.encode('utf-8')

    def get_list_dir(self, path):
        try:
            item = self._getitem(path)
        except:
            return self.format_list_items([])
        
        if not item:
            items = operations.api.get_items()
        else:
            try:
                items = operations.api.get_items(parent_id=item.id)
            except:
                return self.format_list_items([])
        return self.format_list_items(items)

    def format_mlsx(self, basedir, listing, perms, facts, ignore_err=True):
      # find item in cache...
      if basedir in self.dirlistcache:
        fnd = self.dirlistcache[basedir]
        try:
          items = operations.api.get_items(parent_id = fnd.id)
        except:
          items = []
      else:
        if basedir == os.path.sep:
            items = self.get_putio_api_client().File.list()
        else:
            parent_id = self.idfinder.find_item_by_path(pathtoid._utf8(basedir))
            print "parent_id:", parent_id
            items = operations.api.get_items(parent_id=parent_id)

      c = 0
      s = ''
      for i in items:
          print "================================"
          print dir(i)
          print "================================"
          c = c + 1

          type = 'type=file;'

          if 'type' in facts:
              if 'directory' in i.content_type:
                  type = 'type=dir;'

          if 'size' in facts:
              size = 'size=%s;' % i.size  # file size

          ln = "%s%sperm=r;modify=20071029155301;unique=11150051; %s\r\n" % (type, size, i.name)

          if basedir== os.path.sep:
              key = '/%s' % (pathtoid._utf8(i.name))
          else:
              key = '%s/%s' % (pathtoid._utf8(basedir), pathtoid._utf8(i.name))

          self.dirlistcache[key] = i
          print 'key:', key

          yield ln.encode('utf-8')




class HttpOperations(object):
    '''Storing connection object'''
    def __init__(self):
        self.connection = None
        self.username = None

    def get_oauth_token(self, username, password):
        o = {'name':username, 'password':password, 'next':'/'}    
        s = requests.Session()
        r = s.post("https://put.io/login", data=o, timeout=1)
        r = s.get('https://put.io/v2/oauth2/apptoken/329', timeout=1)
        r = s.post('https://put.io/v2/oauth2/authenticate?client_id=329&response_type=oob&redirect_uri=na', data={'allow':'Allow'}, timeout=1)    
        token = ''
        for ln in r.content.split("\n"):
            if 'appsecret' in ln:
                m = re.search('value="(.*?)"', ln)
                if m:
                    token = m.groups()[0]
        return token

    def authenticate(self, username, password):
        token = self.get_oauth_token(username, password)
        if not token:
            return False
        print "> welcome ", username, token
        self.token = token
        return True

    def __repr__(self):
        return self.connection


class HttpAuthorizer(ftpserver.DummyAuthorizer):
    '''FTP server authorizer. Logs the users into Putio Cloud
       Files and keeps track of them.
    '''        
    def __init__(self):        
        self.users = {}
    
    def validate_authentication(self, username, password):        
        try:
            self.operations = HttpOperations()
            self.operations.authenticate(username, password)
            self.users[username] = {'token': self.operations.token, 'user_id': 4}
            return True            
        except:            
            return False

    def has_user(self, username):
        return username != 'anonymous'

    def has_perm(self, username, perm, path=None):
        return True

    def get_perms(self, username):
        return 'lrdw'

    def get_home_dir(self, username):
        return os.sep

    def get_msg_login(self, username):
        return 'Welcome %s' % username

    def get_msg_quit(self, username):
        return 'Goodbye %s' % username

    
def run_ftp_server():
    #    token = ''
    #    client = putio2.Client(token)
    #    files = client.File.list()
    #    print files
    #    return
    ftp_handler = ftpserver.FTPHandler
    ftp_handler.authorizer = HttpAuthorizer()
    ftp_handler.abstracted_fs = HttpFS
    address = (config.ip_address, 2121)
    ftpd = ftpserver.FTPServer(address, ftp_handler)
    ftpd.serve_forever()


if __name__ == '__main__':
    run_ftp_server()

