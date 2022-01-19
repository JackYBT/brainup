
class DataSend(object):
    def __init__(self,id,datas):
        self.id=id
        self.datas=datas
class DataReceive(object):
    def __init__(self,d):
        self.__dict__=d
def handle(d):
    return DataReceive(d['id'],d['datas'])