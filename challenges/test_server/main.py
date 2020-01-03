
from socket import *

s = socket()
s.bind(('0.0.0.0', 3260))
s.listen(6)

while True:
    c, _ = s.accept()
    c.send('foobar')

