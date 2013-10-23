#!/usr/bin/python

import sys
import gobject
import time
import httplib
import socket
import errno
import logging

import debug_logger

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

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


READ_SIZE = 1024 * 32


class GObjectHTTPResponseReader(gobject.GObject):
    def __init__(self, sock, read_amt=-1, *args, **kwargs):
        gobject.GObject.__init__(self)
        # probably move to a StringIO
        self.content = ""
        self.count = 0
        self.read_amt = read_amt
        self.read_buf = ""
        #self.response = NonBlockingHTTPResponse(sock, *args, **kwargs)

    def timeout_callback(self, response):
        self.count += 1
        if response.isclosed():
            print "request hit timeout %s times" % self.count
            return False
        #print "timeout: %s" % self.count
        return True

    def http_callback(self, source, condition, response, read_amt=READ_SIZE, *args):
        #print ".",
        #log.debug("http_callback args %s %s %s" % (source, condition, self.length))
        #path, http_conn, http_response, str(args)
        #print source, path

        # it's faster if we just let it read till it blocks, but setting
        # a read size offers more events.
        #READ_SIZE=-1

        self.read_buf = ""
        buf = ""
        try:
            buf = source.read(read_amt)
        except socket.error, v:
            #log.exception(v)
            if v.errno == errno.EAGAIN:
                log.debug("socket.error: %s" % v)
                return True
            raise

        if read_amt >= 0 and buf >= read_amt:
            log.debug("read up to read_amt %s %s" % (read_amt, len(buf)))
            self.content += buf
            self.read_buf = buf
            return False

        #log.debug("len(buf) %s" % len(buf))
        #print http_conn, http_response, len(buf), http_response.length
        #global finished
        if buf != '':
    #        print "%s read on %s %s" % (len(buf), method, url)
            self.content += buf
    #        self.close()
            return True

        log.debug("----- end")
        response.close()
        log.debug("empty buf")
        log.debug("len:%s len(buf): %s len(content): %s" % (response.length, len(buf), len(self.content)))
        self.finished()
        return False

    def setup_read_callback(self, response):
        # currently no hup, or error callbacks
        self.http_src = gobject.io_add_watch(response.fp, gobject.IO_IN, self.http_callback, response, self.read_amt)

    def setup_timeout_callback(self, response):
        self.timeout_src = gobject.timeout_add(10, self.timeout_callback, response)

    def remove_timeout_callback(self):
        gobject.source_remove(self.timeout_src)

    def finished(self):
        self.remove_timeout_callback()
        if self.finished_callback:
            self.finished_callback()

gobject.type_register(GObjectHTTPResponseReader)


class NonBlockingHTTPResponse(httplib.HTTPResponse):
    def __init__(self, sock, *args, **kwargs):
        httplib.HTTPResponse.__init__(self, sock, *args, **kwargs)
        log.debug("NonBlocking self.fp %s" % (self.fp))
        log.debug("NonBlocking sock %s" % sock)
        self.gresponse = GObjectHTTPResponseReader(sock, *args, **kwargs)

    # need a finish callback
    def do_read(self, amt=-1):
        # read up to amt from the response
        # note if called with amt, the callback is removed, and needs to
        # be setup again
        self.gresponse.read_amt = amt
        self.gresponse.setup_timeout_callback(self)
        self.gresponse.setup_read_callback(self)
        self.gresponse.finished_callback = self.finished_callback
        # loop iteration here till finished callback?

    def finished_callback(self):
        # return all the read content
        self.content = self.gresponse.content
        self._finished_callback()

    def begin(self):
        # HTTPResponse.begin doesnt really deal well with non
        # blocking sockets (some docs point finger at it's use of readline)
        # so, get the response header, with the content length (ie, begin)
        # then set the socket to non blocking
        httplib.HTTPResponse.begin(self)
        self.set_blocking(False)

    def set_blocking(self, blocking=True):
        # HTTPResponse uses a file object like interface to it's socket
        #  (socket._fileobject), so this sets the response objects
        # file object's socket to be non blocking.
        # Almost surely a better way to do this, and it will also depend
        # on the httplib implemtation (ie, httpslib stuff)
        self.fp._sock.setblocking(blocking)


class GobjectHTTPConnection(httplib.HTTPConnection):

    response_class = NonBlockingHTTPResponse

    def __init__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        #GobjectHTTPConnection.__init__(*args, **kwargs)
        self.debuglevel = 0
        self.content = ""
        self.count = 0

    def start_get(self, method, url, body=None, headers={}):
        self.request(method, url, body, headers)
        self.http_response = self.getresponse()
        self.idle_src = gobject.idle_add(self.idle_callback)
        self.http_response._finished_callback = self.read_finished_callback
        self.http_response.do_read()

    def read_finished_callback(self):

        log.debug("removing callbacks")
        log.debug("self.count: %s" % self.count)
        gobject.source_remove(self.idle_src)
        #self.content = self.http_response.content
        log.debug("finished  with len(content): %s" % len(self.http_response.content))

    def error_callback(self, source, *args):
        print "oops", source, str(args)
        return False

    def idle_callback(self, *args):
        log.debug("\t idle callback: %s" % str(args))
        if self.http_response.isclosed():
            log.debug("idle finished")
            return False
       # time.sleep(.3)
        return True


def get(path):
    http_conn = GobjectHTTPConnection(host="127.0.0.1", port=80)
    http_conn.set_debuglevel(5)
    http_conn.start_get("GET", path)
    return False


def setup():
    for path in paths:
        get('/test%s' % path)

    gobject.io_add_watch(sys.stdin, gobject.IO_IN | gobject.IO_HUP, read_stdin_callback)

    return False


def read_stdin_callback(source, condition, *args):
    buf = source.read(8192)
    #print "STDIN:", condition, buf
    if buf == '':
        print "done read stdin"
        return False
    return True


def loop():

    gobject.idle_add(setup)

    # need an exit handler...
    ml = gobject.MainLoop()
    #ml.run()

    # we could run a mainloop.run here, but
    # we need to have a way out
    #
    # this just queues some events, and exits when
    # they (and the io events from the io_add_watch) are done
    ctx = ml.get_context()
    while ctx.pending():
        ctx.iteration()


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
