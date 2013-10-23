#!/usr/bin/python

import sys
import gobject
import time
import httplib
import socket
import errno

import logging
import debug_logger


log = logging.getLogger(__name__)

#paths = ["/2/library/httplib.html"]
    #     "/2/glossary.html"]

paths = ["index.html",
         "/"]

paths = ['/quartz-scheduler/quartz/2.1.5/quartz-2.1.5-sources.jar',
    '/quartz-scheduler/quartz/2.1.5/quartz-2.1.5-javadoc.jar',
    '/quartz-scheduler/quartz/2.1.5/quartz-2.1.5.pom',
    '/quartz-scheduler/quartz/2.1.5/quartz-2.1.5.jar',
    '/quartz-scheduler/quartz/1.8.4/quartz-1.8.4-sources.jar',
    '/quartz-scheduler/quartz/1.8.4/quartz-1.8.4.jar',
    '/quartz-scheduler/quartz/1.8.4/quartz-1.8.4.pom',
    '/quartz-scheduler/quartz/1.8.4/quartz-1.8.4-javadoc.jar',
    '/quartz-scheduler/quartz/1.7.3/quartz-1.7.3.jar',
    '/quartz-scheduler/quartz/1.7.3/quartz-1.7.3.pom',
    '/quartz-scheduler/quartz/1.7.3/quartz-1.7.3-sources.jar',
    '/bouncycastle/bcprov-jdk16/1.46/bcprov-jdk16-1.46.pom',
    '/bouncycastle/bcprov-jdk16/1.46/bcprov-jdk16-1.46-sources.jar',
    '/bouncycastle/bcprov-jdk16/1.46/bcprov-jdk16-1.46.jar',
    '/bouncycastle/bcprov-jdk16/1.46/bcprov-jdk16-1.46-javadoc.jar',
    '/bouncycastle/bcprov-jdk16/1.44/bcprov-jdk16-1.44.jar',
    '/bouncycastle/bcprov-jdk16/1.44/bcprov-jdk16-1.44.pom',
    '/bouncycastle/bcpg-jdk16/1.44/bcpg-jdk16-1.44.jar',
    '/bouncycastle/bcpg-jdk16/1.44/bcpg-jdk16-1.44.pom',
    '/bouncycastle/cp-bouncycastle/1.44/cp-bouncycastle-1.44.jar']


class GobjectHTTPResponse(httplib.HTTPResponse):
    def __init__(self, sock, *args, **kwargs):
        httplib.HTTPResponse.__init__(self, sock, *args, **kwargs)
        self.content = ""
        self.count = 0
        log.debug("self.fp %s" % self.fp)
        log.debug("sock %s" % sock)
        self.sock = sock
        self.set_blocking(False)
        self.setup_callbacks(*args)

    def set_blocking(self, blocking=True):
        self.sock.setblocking(blocking)

    def http_callback(self, source, condition, *args):
        #print ".",
        #log.debug("http_callback args %s %s %s" % (source, condition, self.length))
        #path, http_conn, http_response, str(args)
        #print source, path

        try:
            buf = source.read()
        except socket.error, v:
            log.exception(v)
            if v.errno == errno.EAGAIN:
                log.debug("socket.error: %s" % v)
                return True
            raise


        #log.debug("len(buf) %s" % len(buf))
        #print http_conn, http_response, len(buf), http_response.length
        #global finished
        if buf != '':
    #        print "%s read on %s %s" % (len(buf), method, url)
            self.content += buf
    #        self.close()
            return True

        log.debug("----- end")
        self.close()
        log.debug("empty buf")
        log.debug("len:%s len(buf): %s len(content): %s" % (self.length, len(buf), len(self.content)))
        #self.finished()
        return False

    def timeout_callback(self):
        self.count += 1
        if self.isclosed():
            print "request hit timeout %s times" % self.count
            return False
        #print "timeout: %s" % self.count
        return True

    def setup_callbacks(self, *args):
        self.http_src = gobject.io_add_watch(self.fp, gobject.IO_IN, self.http_callback, *args)
        self.timeout_src = gobject.timeout_add(10, self.timeout_callback)

        self.set_blocking(False)


class GobjectHTTPConnection(httplib.HTTPConnection):

    response_class = GobjectHTTPResponse

    def __init__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        #GobjectHTTPConnection.__init__(*args, **kwargs)
        self.debuglevel = 0
        self.content = ""
        self.count = 0

    #def connect(self):
    #    """Connect to the host and port specified in __init__."""
    #    self.sock = socket.create_connection((self.host, self.port),
    #                                           self.timeout)
        #self.sock.setblocking(False)

    #def getresponse(self):
    #    response = httplib.HTTPConnection.getresponse(self)
        #self.sock.setblocking(False)
    #    return response

    def get(self, method, url, body=None, headers={}):
        self.request(method, url, body, headers)
        self.http_response = self.getresponse()
#        self.http_response.setup_callbacks(method, url)
        #self.http_response.sock.setblocking(False)
        self.idle_src = gobject.idle_add(self.idle_callback)
        #self.timeout_src = gobject.timeout_add(100, self.timeout_callback)

    def finished(self):
        log.debug("removing callbacks")
        log.debug("self.count: %s" % self.count)
        gobject.source_remove(self.idle_src)
        gobject.source_remove(self.timeout_src)

    def error_callback(self, source, *args):
        print "oops", source, str(args)
        return False

    def idle_callback(self, *args):
        log.debug("\t idle callback: %s" % str(args))
        if self.http_response.isclosed():
            log.debug("idle finished")
            return False
        time.sleep(.3)
        return True



def get(path):
    http_conn = GobjectHTTPConnection(host="127.0.0.1", port=80)
    http_conn.set_debuglevel(5)
    #http_conn.connect()
    #conn.request("GET", path)
    http_conn.get("GET", path)
    return False


def setup():
    #fo = open("/tmp/foo", "r")
    #gobject.io_add_watch(fo, gobject.IO_IN, callback)
#    gobject.io_add_watch(sys.stdin, gobject.IO_IN|gobject.IO_HUP, callback)
    for path in paths:
        get('/test%s' % path)

    return False


def loop():
    gobject.idle_add(setup)
    ml = gobject.MainLoop()
    ml.run()
    #ctx = ml.get_context()
    #while ctx.pending():
    #    ctx.iteration()


def main():
    loop()
#    gobject.MainLoop().run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print "exit"
        sys.exit(1)
    sys.exit()
