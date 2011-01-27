# encoding: utf-8
import putio
import config
import os

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

sep = os.path.sep
sepsep = sep + sep

class PathToId:

  def __init__(self):
    self.cache = {sepsep:0, sep:0}
    self.itemscache = {}
    self.api = None 

  def encode_key(self, s):
    return _utf8(s)

  def get_items_cache(self, parent_id=0):
    if parent_id in self.itemscache:
      return self.itemscache[parent_id]
    return False

  def load_items(self, path=sep, parent_id=0):
    
    try:
      if self.get_items_cache(parent_id):
        items = self.get_items_cache(parent_id)
      else:
        self.api = putio.Api(config.apikey, config.apisecret)
        items = self.api.get_items(parent_id=parent_id)
        self.itemscache[parent_id] = items
    except: #     raise PutioError("You have no items to show.") for empty folders ? wtf.
      items = []
      
    for i in items:
      key = self.encode_key(_utf8(path) + sep + _utf8(i.name) )
      self.cache[key] = i.id

  def find_item_by_path(self, path):
    # this is root
    if path == sep:
      return 0

    if not path.startswith(sep):
      raise ValueError('parse_fspath: You have to provide a full path')

#    if not path.startswith('//'):
#      path = '/' + path

    parents = path.split(sep)[1:]
    # check if they are cached or not...
    k = sep
    lparentid = 0
    lparentpath = ''
    for dir in parents:
      self.load_items(k, self.cache[self.encode_key(k)])
      k = k + sep + dir
      print k
    self.load_items(k, self.cache[self.encode_key(k)])

    return self.cache[self.encode_key(sep + _utf8(path) )]


if __name__ == '__main__':
  api = putio.Api(config.apikey, config.apisecret)
  items = api.get_items(parent_id=24, limit=300)
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


