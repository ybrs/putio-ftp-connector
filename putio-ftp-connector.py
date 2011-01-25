#!/usr/bin/env python
# $Id: basic_ftpd.py 569 2009-04-04 00:17:43Z billiejoex $

"""A basic FTP server which uses a DummyAuthorizer for managing 'virtual
users', setting a limit for incoming connections.
"""

import os

#from pyftpdlib
import ftpserver
import urllib2
import base64

import putio
from pathtoid import PathToId
import pathtoid
import config

import pycurl

class HttpFD(object):

    def __init__(self, apifile, bucket, obj, mode):

        self.apifile = apifile
        self.download_url = apifile.get_stream_url()
        self.bucket = bucket
        self.name = obj
        self.mode = mode
        self.closed = False
        self.total_size = None

        self.read_size = 0
        # speed...
        self.read_bytes = 128 * 1024 # 128kb per iteration
        self.buffer = ''
        self.req = None
        self.fd = None

#        if not all([username, bucket, obj]):
#            self.closed = True
#            raise IOError(1, 'Operation not permitted')
#
#        try:
#            self.bucket = \
#                operations.connection.get_bucket(self.bucket)
#        except:
#            raise IOError(2, 'No such file or directory')
#
#        if 'r' in self.mode:
#            try:
#                self.obj = self.bucket.get_key(self.name)
#            except:
#                raise IOError(2, 'No such file or directory')
#        else: #write
#            self.obj = self.bucket.get_key(self.name)
#            if not self.obj:
#                # key does not exist, create it
#                self.obj = self.bucket.new_key(self.name)
#            # create a temporary file
#            self.temp_file_path = tempfile.mkstemp()[1]
#            self.temp_file = open(self.temp_file_path, 'w')


#        c = pycurl.Curl()
#        print "download_url >> ", self.download_url
#        c.setopt(pycurl.URL, self.download_url.encode('utf-8'))
#        c.setopt(c.WRITEFUNCTION, self.curl_write_func)
#        c.perform()
#        c.close()

        # gets total size
        req = urllib2.Request(self.download_url)
        f = urllib2.urlopen(req)
        self.total_size = f.headers.get('Content-Length')




    def write(self, data):
        raise OSError(1, 'Operation not permitted')
        # self.temp_file.write(data)

    def close(self):
        return
        self.temp_file.close()
        self.obj.set_contents_from_filename(self.temp_file_path)
        self.obj.close()

        # clean up the temporary file
        os.remove(self.temp_file_path)
        self.temp_file_path = None
        self.temp_file = None

    def curl_write_func(self, buf):
        self.buffer = self.buffer + buf

    def __read(self, size=65536):
        c =  self.buffer
        self.buffer = ''
        return c


    def read(self, size=65536):
        # req = urllib2.Request('https://www.put.io/download-file/4/11150051')
        if self.req == None:
            self.req = urllib2.Request(self.download_url)

#        username = ''
#        password = ''
#        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
#        req.add_header("Authorization", "Basic %s" % base64string)

        read_next = self.read_size + self.read_bytes

#        req.headers['Range'] = 'bytes=%s-%s' % (self.read_size, read_next)
#
#        print "range:", req.headers['Range']

        if self.total_size == None:
          pass
#          f = urllib2.urlopen(req)
#          range=f.headers.get('Content-Range')
#          # bytes 0-10/26
#          self.total_size = int(range.split('/')[1])

        #print "readsize > totalsize", self.read_size, self.total_size

        if self.read_size > self.total_size:
          return

        self.read_size = self.read_size + self.read_bytes + 1
        if not self.fd:
            self.fd = urllib2.urlopen(self.req)

        return self.fd.read(1024)

        #return self.obj.read()

    def seek(self, *kargs, **kwargs):
        print ">>>>>>>>>> seek"
        raise IOError(1, 'Operation not permitted')

# ....
idfinder = PathToId()
idfinder.load_items()

api = None


class HttpFS(ftpserver.AbstractedFS):



    def __init__(self):
        self.root = None
        self.cwd = '/'
        self.rnfr = None
        self.dirlistcache = {}
        self.idfinder = idfinder

#    def parse_fspath(self, path):
#        '''Returns a (username, site, filename) tuple. For shorter paths
#replaces not provided values with empty strings.
#'''
#        if not path.startswith(os.sep):
#            raise ValueError('parse_fspath: You have to provide a full path')
#        parts = path.split(os.sep)[1:]
#        if len(parts) > 3:
#            # join extra 'directories' into key
#            parts = parts[0], parts[1], os.sep.join(parts[2:])
#        while len(parts) < 3:
#            parts.append('')
#        return tuple(parts)


    def open(self, filename, mode):
        print "filename: ", filename
#        username, bucket, obj = self.parse_fspath(filename)

        if filename in self.dirlistcache:
          print 'found............'
          apifile = self.dirlistcache[filename]
          print 'found........', apifile.id, apifile.name

        else:
          if filename == '/':
            items = operations.api.get_items()
          else:
            id = idfinder.find_item_by_path(filename)
            print "file id:", id
            apifile = operations.api.get_items(id=id)[0]

        print apifile.get_download_url()

        #
        return HttpFD(apifile, None, filename, mode)

    def chdir(self, path):
        print ">>>>>>>>>>>>> chdir:" , path
        print ">>>>>>>>>>>>>  root:", self.root
        self.cwd = path.decode('utf-8').encode('utf-8')
        print ">>>>>>>>>>>> cwd:", self.cwd, type(self.cwd)
        return
#        if path.startswith(self.root):
#            _, bucket, obj = self.parse_fspath(path)
#
#            if not bucket:
#                self.cwd = self.fs2ftp(path)
#                return
#
#            if not obj:
#                try:
#                    operations.connection.get_bucket(bucket)
#                    self.cwd = self.fs2ftp(path)
#                    return
#                except:
#                    raise OSError(2, 'No such file or directory')
#
#        raise OSError(550, 'Failed to change directory.')

    def mkdir(self, path):
        try:
            _, bucket, obj = self.parse_fspath(path)
            if obj:
                raise OSError(1, 'Operation not permitted')
        except(ValueError):
            raise OSError(2, 'No such file or directory')

        operations.connection.create_bucket(bucket)

    def listdir(self, path):
      return ['a1.txt', 'b1.txt', 'c1.txt']
#        try:
#            _, bucket, obj = self.parse_fspath(path)
#        except(ValueError):
#            raise OSError(2, 'No such file or directory')
#
#        if not bucket and not obj:
#            return operations.connection.get_all_buckets()
#
#        if bucket and not obj:
#            try:
#                cnt = operations.connection.get_bucket(bucket)
#                return cnt.list()
#            except:
#                raise OSError(2, 'No such file or directory')

    def rmdir(self, path):
        _, bucket, name = self.parse_fspath(path)

        if name:
            raise OSError(13, 'Operation not permitted')

        try:
            bucket = operations.connection.get_bucket(bucket)
        except:
            raise OSError(2, 'No such file or directory')

        try:
            operations.connection.delete_bucket(bucket)
        except:
            raise OSError(39, "Directory not empty: '%s'" % bucket)

    def remove(self, path):
        _, bucket, name = self.parse_fspath(path)

        if not name:
            raise OSError(13, 'Operation not permitted')

        try:
            bucket = operations.connection.get_bucket(bucket)
            bucket.delete_key(name)
        except:
            raise OSError(2, 'No such file or directory')
        return not name

    def rename(self, src, dst):
        raise OSError(1, 'Operation not permitted')

    def isfile(self, path):
        return not self.isdir(path)

    def islink(self, path):
        return False

    def isdir(self, path):
      print "path:", path
      return True
#        _, _, name = self.parse_fspath(path)
#        return not name

    def getsize(self, path):
        return self.stat(path).st_size

    def getmtime(self, path):
        return self.stat(path).st_mtime

    def realpath(self, path):
        return path

    def lexists(self, path):
        try:
            _, bucket, obj = self.parse_fspath(path)
        except(ValueError):
            raise OSError(2, 'No such file or directory')

        if not bucket and not obj:
            buckets = operations.connection.get_all_buckets()
            return bucket in buckets

        if bucket and not obj:
            try:
                cnt = operations.connection.get_bucket(bucket)
                objects = cnt.list()
            except:
                raise OSError(2, 'No such file or directory')
            return obj in objects

    def stat(self, path):
        _, bucket, name = self.parse_fspath(path)
        if not name:
            raise OSError(40, 'unsupported')
        try:
            bucket = operations.connection.get_bucket(bucket)
            obj = bucket.get_key(name)
            return os.stat_result((666, 0L, 0L, 0, 0, 0, obj.size, 0, 0, 0))
        except:
            raise OSError(2, 'No such file or directory')

    exists = lexists
    lstat = stat

    def validpath(self, path):
        return True

    def get_list_dir(self, path):
        try:
            _, bucket, obj = self.parse_fspath(path)
        except(ValueError):
            raise OSError(2, 'No such file or directory')

        if not bucket and not obj:
            buckets = operations.connection.get_all_buckets()
            return self.format_list_buckets(buckets)

        if bucket and not obj:
            try:
                cnt = operations.connection.get_bucket(bucket)
                objects = cnt.list()
            except:
                raise OSError(2, 'No such file or directory')
            return self.format_list_objects(objects)

    def format_list_objects(self, items):
        for item in items:
            ts = datetime.datetime(
                *time.strptime(
                    item.last_modified[:item.last_modified.find('.')],
                    "%Y-%m-%dT%H:%M:%S")[0:6]).strftime("%b %d %H:%M")

            yield '-rw-rw-rw- 1 %s group %8s %s %s\r\n' % \
                (operations.username, item.size, ts, item.name)

    def format_list_buckets(self, buckets):
        for bucket in buckets:
            yield 'drwxrwxrwx 1 %s group %8s Jan 01 00:00 %s\r\n' % \
                (operations.username, 0, bucket.name)

    def get_stat_dir(self, *kargs, **kwargs):
        raise OSError(40, 'unsupported')

    def format_mlsx(self, basedir, listing, perms, facts, ignore_err=True):

      print 'facts', facts
      print 'basedir', basedir
      print 'listing', listing

      # find item in cache...
      if basedir in self.dirlistcache:
        print 'found............'
        fnd = self.dirlistcache[basedir]
        print 'found........', fnd.id, fnd.name
        try:
          items = operations.api.get_items(parent_id = fnd.id)
        except:
          items = []
      else:
        if basedir == '/':
          items = operations.api.get_items()
        else:
          parent_id = self.idfinder.find_item_by_path(pathtoid._utf8(basedir))
          print "parent_id:", parent_id
          items = operations.api.get_items(parent_id=parent_id)


      c = 0
      s = ''
      for i in items:
          c = c + 1

          type = 'type=file;'

          if 'type' in facts:
            if i.type == 'folder':
              type = 'type=dir;'

          if 'size' in facts:
              size = 'size=%s;' % i.size  # file size

          ln = "%s%sperm=r;modify=20071029155301;unique=11150051; %s\r\n" % (type, size, i.name)

          if basedir=='/':
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

    def authenticate(self, username, password):
        self.username = username
        self.password = password
        config.apisecret = password
        config.apikey    = username
        print "here !..............."
        self.api = putio.Api(config.apikey,config.apisecret)
        return True


    def __repr__(self):
        return self.connection

operations = HttpOperations()


class HttpAuthorizer(ftpserver.DummyAuthorizer):
    '''FTP server authorizer. Logs the users into Putio Cloud
Files and keeps track of them.
'''
    users = {}

    def validate_authentication(self, username, password):
        try:
            operations.authenticate(username, password)
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



def main():

      ftp_handler = ftpserver.FTPHandler
      ftp_handler.authorizer = HttpAuthorizer()
      ftp_handler.abstracted_fs = HttpFS
#      ftp_handler.passive_ports = range(60000, 65535)
#      try:
#          ftp_handler.masquerade_address = gethostbyname(options.bind_address)
#      except gaierror, (_, errmsg):
#          sys.exit('Address error: %s' % errmsg)
#
#      ftpd = ftpserver.FTPServer((options.bind_address,
#                                  options.port),
#                                 ftp_handler)

      address = ('', 2121 )
      ftpd = ftpserver.FTPServer(address, ftp_handler)
      ftpd.serve_forever()


#    # Instantiate a dummy authorizer for managing 'virtual' users
#    authorizer = ftpserver.DummyAuthorizer()
#
#    # Define a new user having full r/w permissions and a read-only
#    # anonymous user
#    authorizer.add_user('user', '12345', '/home/aybars/completed', perm='elradfmw')
#    authorizer.add_anonymous('/home/aybars/completed')
#
#    # Instantiate FTP handler class
#    ftp_handler = ftpserver.FTPHandler
#    ftp_handler.authorizer = authorizer
#
#    # Define a customized banner (string returned when client connects)
#    ftp_handler.banner = "pyftpdlib %s based ftpd ready." %ftpserver.__ver__
#
#    # Specify a masquerade address and the range of ports to use for
#    # passive connections.  Decomment in case you're behind a NAT.
#    #ftp_handler.masquerade_address = '151.25.42.11'
#    #ftp_handler.passive_ports = range(60000, 65535)
#
#    # Instantiate FTP server class and listen to 0.0.0.0:21
#    address = ('', 2121 )
#    ftpd = ftpserver.FTPServer(address, ftp_handler)
#
#    # set a limit for connections
#    ftpd.max_cons = 256
#    ftpd.max_cons_per_ip = 5
#
#    # start ftp server
#    ftpd.serve_forever()




if __name__ == '__main__':

#    api = putio.Api(config.apikey, config.apisecret)
#
#    # getting your items
#    items = api.get_items(parent_id=11110932)
#    #yield items
#
#    for it in items:
#        print "%s  %s" % (it.id, it.name)


    main()
