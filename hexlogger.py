import logging

class HLogger (logging.Logger) :

  @staticmethod
  def getLogger(cname: str) :
    if isinstance(logging.getLoggerClass(), HLogger):
      return logging.getLogger(cname)
    else:
      logging.setLoggerClass(HLogger)
      return logging.getLogger(cname)
  

  def __init__(self, name: str) -> None:
    super().__init__(name)
    hFormatter = logging.Formatter('%(asctime)s::%(levelname)s::%(name)s::@Line::%(lineno)d::%(message)s',datefmt="%m/%d/%Y %H:%M:%S",)
    f_handlr = logging.FileHandler("hex-assess-app.log")
    f_handlr.setFormatter(hFormatter)
    self.setLevel(logging.DEBUG)
    self.addHandler(f_handlr)
