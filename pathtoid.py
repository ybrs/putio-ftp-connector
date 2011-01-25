# encoding: utf-8
import putio
import config

def _unicode(s):
    if isinstance(s, str):
        try:
            return s.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPError(400, "Non-utf8 argument")
    assert isinstance(s, unicode)
    return s

def _utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8")
    assert isinstance(s, str)
    return s

class PathToId:

  def __init__(self):
    self.cache = {'//':0, '/':0}



  def encode_key(self, s):
    return _utf8(s)

  def load_items(self, path='/', parent_id=0):
    api = putio.Api(config.apikey, config.apisecret)

    # TODO: cache the items will you ?
    try:
      items = api.get_items(parent_id=parent_id)
    except: #     raise PutioError("You have no items to show.") for empty folders ? wtf.
      items = []
      
    for i in items:
      key = self.encode_key(_utf8(path) + '/' + _utf8(i.name) )
      self.cache[key] = i.id

  def find_item_by_path(self, path):
    # this is root
    if path == '/':
      return 0

    if not path.startswith('/'):
      raise ValueError('parse_fspath: You have to provide a full path')

#    if not path.startswith('//'):
#      path = '/' + path

    parents = path.split('/')[1:]
    # check if they are cached or not...
    k = '/'
    lparentid = 0
    lparentpath = ''
    for dir in parents:
      self.load_items(k, self.cache[self.encode_key(k)])
      k = k + '/' + dir
      print k
    self.load_items(k, self.cache[self.encode_key(k)])

    return self.cache[self.encode_key('/' + _utf8(path) )]


if __name__ == '__main__':
  api = putio.Api(config.apikey, config.apisecret)
  items = api.get_items()
  for i in items:
    print ">", i.id, i.name.encode('utf-8')

#  p = PathToId()
#  #p.load_items('/x', 11156055)
#  p.load_items()
#  print "============================="
#  print p.find_item_by_path('/x/y/z/rtorrent.log')
#  print p.find_item_by_path('/x/y/z')
  #p.find_item_by_path('/x/y/z')

#  s = 'çöğüışIĞÜÇÖ'.decode('utf-8')
#  print s, type(s)
  