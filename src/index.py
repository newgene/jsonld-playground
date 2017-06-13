import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from subprocess import Popen, PIPE, STDOUT
import json

from config import RUBY_JSONLD_CMD

doc = json.dumps({
    "@context": {
        "name": "http://xmlns.com/foaf/0.1/name",
        "homepage": "http://xmlns.com/foaf/0.1/homepage",
        "avatar": "http://xmlns.com/foaf/0.1/avatar"
    },
    "name": "Manu Sporny",
    "homepage": "http://manu.sporny.org/",
    "avatar": "http://twitter.com/account/profile_image/manusporny"
})

def process_jsonld(doc, action="expand", frame=None):
    #cmd = 'ruby jsonld_test_cli.rb -a compact'
    cmd = RUBY_JSONLD_CMD + ' '
    if action == 'expand':
        cmd += '--expand'
    elif action == 'compact':
        cmd += '--compact'
    elif action == 'flatten':
        cmd += '--flatten'
    elif action == 'frame':
        cmd += '--frame ./default_frame.jsonld'
    elif action == 'nquads':
        cmd += '--validate --format nquads'
    elif action == 'normalize':
        cmd += '--validate --format nquads'
    else:
        raise ValueError("Unknown action")

    p = Popen(cmd.split(), stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    p.stdin.write(doc.encode('utf-8'))
    #stdout_data = p.communicate(input=doc.encode('utf-8'))[0]
    stdout_data = p.communicate()[0]
    p.stdin.close()
    return stdout_data.decode()


define("port", default=8000, help="run on the given port", type=int)
define("address", default="127.0.0.1", help="run on localhost")
define("debug", default=False, type=bool, help="run in debug mode")

try:
    options.parse_command_line()
except:
    pass

if options.debug:
    import tornado.autoreload
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    options.address = '0.0.0.0'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        doc = self.request.body.decode()
        action = self.get_argument('action', 'expand')
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps({"output": process_jsonld(doc, action=action)}))


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/?(.*)", tornado.web.StaticFileHandler, {'path': './'})
    ], debug=options.debug)


if __name__ == "__main__":
    app = make_app()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port, address=options.address)
    loop = tornado.ioloop.IOLoop.instance()
    if options.debug:
        tornado.autoreload.watch('./index.html')
        tornado.autoreload.start(loop)
        logging.info('Server is running on "%s:%s"...' % (options.address, options.port))
    loop.start()