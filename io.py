#!/usr/bin/python

import sys
import gobject
import time
import httplib
import socket
import errno

finished = None
global finished


paths = ["/2/library/httplib.html"]
    #     "/2/glossary.html"]

def idle_callback(*args):
    print "\t\tidle", str(args)
    global finished
    if finished:
        print "idle finished"
        return False
    time.sleep(.01)
    return True

class GobjectHTTPResponse(httplib.HTTPResponse):
    pass


class GobjectHTTPConnection(httplib.HTTPConnection):

    #response_class = GobjectHTTPResponse

    def __init__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        #GobjectHTTPConnection.__init__(*args, **kwargs)
        self.debuglevel = 5
        self.content = ""

    def connect(self):
        """Connect to the host and port specified in __init__."""
        self.sock = socket.create_connection((self.host, self.port),
                                               self.timeout)
        #self.sock.setblocking(False)

    def getresponse(self):
        response = httplib.HTTPConnection.getresponse(self)
        self.sock.setblocking(False)
        return response

    def callback(self, source, *args):
        global finished
        #print "source", source
        print "args", str(args)
        buf = source.read(500)
        print "buf", buf
        if buf == '':
            finished = True
            print "callback finished"
            return False
        return True

    def http_callback(self, source, condition, path, http_conn, http_response, *args):
        print "http_callback args", source, condition, http_response.length
        #path, http_conn, http_response, str(args)
        #print source, path

        try:
            buf = source.read()
        except socket.error, v:
            if v.errno == errno.EAGAIN:
                print "socket.error: %s" % v
                return True
            raise

        print buf
        #print http_conn, http_response, len(buf), http_response.length
        #global finished
        if buf != '':
            self.content += buf
            self.close()
            return True

        print http_response.length, len(buf), len(self.content)
        self.finished()
        return False

    def finished(self):
        global finished
        finished = True
        print "foo", self.content

    def error_callback(self, source, *args):
        print "oops", source, str(args)
        global finished
        finished = True
        return False


def get(path):
    http_conn = GobjectHTTPConnection(host="www.redhat.com", port=80)
    print "http_conn", http_conn, dir(http_conn)
    http_conn.set_debuglevel(5)
    #http_conn.connect()
    #conn.request("GET", path)
    http_conn.request("GET", path)
    response = http_conn.getresponse()
    http_conn.sock.setblocking(0)
    gobject.io_add_watch(response.fp, gobject.IO_IN|gobject.IO_HUP, http_conn.http_callback, path, http_conn, response)
#    gobject.io_add_watch(response.fp, gobject.IO_ERR, http_conn.error_callback)


def setup():
    #fo = open("/tmp/foo", "r")
    gobject.idle_add(idle_callback)
    #gobject.io_add_watch(fo, gobject.IO_IN, callback)
#    gobject.io_add_watch(sys.stdin, gobject.IO_IN|gobject.IO_HUP, callback)
    for path in paths:
        print "getting", path
        get(path)


def loop():
    ml = gobject.MainLoop()
    ctx = ml.get_context()
    while ctx.pending():
        ctx.iteration()


def main():
    setup()
    loop()
#    gobject.MainLoop().run()


if __name__ == "__main__":
    main()
    sys.exit()
