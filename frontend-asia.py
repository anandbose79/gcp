

import BaseHTTPServer
from multiprocessing import Process
import os
import SocketServer
import sys
import time

REQUEST_CPUTIME_SEC = 1.0
REQUEST_TIMEOUT_SEC = 5.0


class CpuBurner(object):
    def get_walltime(self):
        return time.time()

    def get_user_cputime(self):
        return os.times()[0]

    def busy_wait(self):
        for _ in xrange(100000):
            pass

    def burn_cpu(self):

        start_walltime_sec = self.get_walltime()
        start_cputime_sec = self.get_user_cputime()
        while (self.get_user_cputime() <
               start_cputime_sec + REQUEST_CPUTIME_SEC):
            self.busy_wait()
            if (self.get_walltime() >
                    start_walltime_sec + REQUEST_TIMEOUT_SEC):
                sys.exit(1)

    def handle_http_request(self):
        start_time = self.get_walltime()
        p = Process(target=self.burn_cpu)  # Run in a separate process.
        p.start()
        # Force kill after timeout + 1 sec.
        p.join(timeout=REQUEST_TIMEOUT_SEC + 1)
        if p.is_alive():
            p.terminate()
        if p.exitcode != 0:
            return (500, "Request failed\n")
        else:
            end_time = self.get_walltime()
            response = "Asia Request took %.2f walltime seconds\n" % (
                end_time - start_time)
            return (200, response)


class DemoRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        mapping = {
            "/": lambda: (200, "OK Asia"),  # Return HTTP 200 response.
            "/service": CpuBurner().handle_http_request,
        }
        if self.path not in mapping:
            self.send_response(404)
            self.end_headers()
            return
        (code, response) = mapping[self.path]()
        self.send_response(code)
        self.end_headers()
        self.wfile.write(response)
        self.wfile.close()


class DemoHttpServer(SocketServer.ThreadingMixIn,
                     BaseHTTPServer.HTTPServer):
    pass


if __name__ == "__main__":
    httpd = DemoHttpServer(("", 80), DemoRequestHandler)
    httpd.serve_forever()
