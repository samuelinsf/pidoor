#!/usr/bin/python

import wsgiref.simple_server
import lazytable
import json
import os
import cgi
import Cookie
import base64
import hmac
import struct
import time
import socket
import BaseHTTPServer
import optparse
import ConfigParser

CONFIG = {}

COOKIE_NAME = 'door'
LOG_DB_SUFFIX = '_log.sqlite'

example_config = """
#
# web_ui.ini example
#   config file for the pidoor web ui
#

[web_ui]
port: 8000
data_path: /data

# this can be any random value, it is used to 
# sign the nonce cookies given to users, if you steal this, you
# can forge logged in session cookies, likewise to log out all users
# change this value
secret: YN4VVVVVVKKKX

# the username one needs to use to login to the admin console
username: admin

# This is the hash of the password used to authenticate logins
# (so the plaintext password doesn't live in this file)
# make with;
# python -c 'import hmac; print hmac.new(password_salt, "password").hexdigest()'
password_salt: xxxxxyyyyccvbg
hex_hmac_passwd: 743f55bbb000000000000000770000c3

# 2 yr timeout = (3600 * 24 * 365 * 2) = 63072000
login_time: 63072000 
"""

login_form = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>doors</title>

        <!-- Latest compiled and minified CSS -->
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">

        <STYLE TYPE="text/css">
            <!--
            body {
                padding-top: 40px;
                padding-bottom: 40px;
                background-color: #eee;
            }

            .form-signin {
                max-width: 330px;
                padding: 15px;
                margin: 0 auto;
            }
            .form-signin .form-signin-heading,
            .form-signin .checkbox {
                margin-bottom: 10px;
            }
            .form-signin .checkbox {
                font-weight: normal;
            }
            .form-signin .form-control {
                position: relative;
                height: auto;
                -webkit-box-sizing: border-box;
                -moz-box-sizing: border-box;
                box-sizing: border-box;
                padding: 10px;
                font-size: 16px;
            }
            .form-signin .form-control:focus {
                z-index: 2;
            }
            .form-signin input[type="email"] {
                margin-bottom: -1px;
                border-bottom-right-radius: 0;
                border-bottom-left-radius: 0;
            }
            .form-signin input[type="password"] {
                margin-bottom: 10px;
                border-top-left-radius: 0;
                border-top-right-radius: 0;
            }
            -->
        </style>

        <!-- Optional theme -->
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap-theme.min.css">

        <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
        <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
        <!--[if lt IE 9]>
            <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
            <script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>
        <![endif]-->
    </head>
    <body>
        <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
        <!-- Latest compiled and minified JavaScript -->
        <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>

        <div class="container">
            <form class="form-signin" role="form" method="post" action="%(path)s">
                <h2 class="form-signin-heading">%(msg)s</h2>
                <input name="login_username" type="text" class="form-control" placeholder="Login" required autofocus>
                <input name="login_password" type="password" class="form-control" placeholder="Password" required>
                <button class="btn btn-lg btn-primary btn-block" type="submit">login</button>
            </form>
        </div> <!-- /container -->

    </body>
</html>
"""

page_top = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>doors</title>

        <!-- Latest compiled and minified CSS -->
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">

        <!-- Optional theme -->
        <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap-theme.min.css">

        <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
        <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
        <!--[if lt IE 9]>
            <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
            <script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>
        <![endif]-->
    </head>
    <body>
        <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
        <!-- Latest compiled and minified JavaScript -->
        <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>

        <div class="container">

            <div class="starter-template">
                <h1></h1>
                <div class="lead">
                    <a href="%(path)s">
                        doors %(now)s
                    </a>
                </div>
            </div>

"""

page_end = """
            <div class="lead row col-md-8 pull-right">
                <a href="%(path)s?logout=1">
                   [logout]
                </a>
            </div>
        </div> <!-- container -->
    </body>
</html>

"""

def process_login_form(environ, headers, msg=''):
    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    form = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    user = form.getfirst("login_username", "")
    passwd = form.getfirst("login_password", "")
    if (user == CONFIG['username'] and hmac.new(CONFIG['password_salt'], passwd).hexdigest() == CONFIG['hex_hmac_passwd']):
        # login is good, set cookie
        if 'HTTP_COOKIE' in environ:
            c = Cookie.SimpleCookie(environ['HTTP_COOKIE'])
        else:
            c = Cookie.SimpleCookie()
        nonce = open('/dev/urandom', 'rb').read(8)
        valid_until = struct.pack('Q', int(time.time()) + CONFIG['login_time'])
        hsecret = hmac.new(nonce + valid_until, CONFIG['secret']).digest()
        h = nonce + valid_until + hsecret
        c[COOKIE_NAME] = base64.urlsafe_b64encode(h)
        c[COOKIE_NAME]['domain'] = environ['HTTP_HOST'].split(':')[0]
        c[COOKIE_NAME]['expires'] = CONFIG['login_time']
        headers.extend(("Set-cookie", morsel.OutputString()) for morsel in c.values())
        return (True, headers, [])

    if user != '' or passwd != '':
        msg = 'incorrect username or password'

    return (False, headers, [login_form % ({'path':path(environ), 'msg':msg})])

def check_or_do_login(environ):
    login_ok = False
    output = []
    headers = []
    if 'HTTP_COOKIE' in environ:
        c = Cookie.SimpleCookie(environ['HTTP_COOKIE'])
        if ('QUERY_STRING' in environ) and (environ['QUERY_STRING'] == 'logout=1'):
            c[COOKIE_NAME] = ''
            c[COOKIE_NAME]['domain'] = environ['HTTP_HOST'].split(':')[0]
            c[COOKIE_NAME]['expires'] = CONFIG['login_time']
            headers.extend(("Set-cookie", morsel.OutputString()) for morsel in c.values())
        elif (COOKIE_NAME in c) and (len(c[COOKIE_NAME].value) > 8):
            h = base64.urlsafe_b64decode(c[COOKIE_NAME].value)
            (nonce, valid_until, hsecret) = (h[:8], h[8:16], h[16:])
            digest = hmac.new(nonce + valid_until, CONFIG['secret']).digest()
            if digest == hsecret and struct.unpack('Q', valid_until)[0] > time.time():
                login_ok = True

    if not login_ok:
        (login_ok, headers, output) = process_login_form(environ, headers)

    return (login_ok, headers, output)


def time_dhms(seconds):
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        r = '%dd %02d:%02d:%02d' % (days, hours, minutes, seconds)
    else:
        r = '%02d:%02d:%02d' % (hours, minutes, seconds)
    return r
    
def open_durations(log):
    r = []
    l = []
    for e in log:
        l.append(e)
    while l and l[0]['event'] == 'loop_open':
        l = l[1:]
    while l:
        close = l.pop(0)
        while l and l[0]['event'] == 'loop_closed':
            close = l.pop(0)
        if not l:
            break
        open = l.pop(0)
        r.append({'human_time':close['human_time'], 'open':close['wall_time'] - open['wall_time']})
    return r
        
        
def dedup_last(log):
    # colapse repeated events to oldest in log event list
    if 'event' not in log[0]:
        return log[0]
    last = log[0]
    for e in log:
        if last['event'] != e['event']:
            return last
        else:
            last = e
        
def render_dropdowns(logs):
    n = 0
    r = []
    for name, log in sorted(logs.items()):
        n += 1
        color = 'success'
        last = dedup_last(log)
        if last.get('event', '') == 'loop_open':
            color = 'danger'
        if 'card' in last:
            summary = ' %s %s ago' % (last.get('card_note', '??'), time_dhms(time.time() - last['wall_time']))
        else:
            summary = ' %s ago' % (time_dhms(time.time() - last['wall_time']))
        r.append ("""
            <div class="panel panel-%s">
                <div class="panel-heading">
                    <h4 class="panel-title">
                        <a data-toggle="collapse" href="#collapse_%d">
                            %s
                        </a>
                    </h4>
                </div>
                <ul id=collapse_%d class="list-group collapse ">
        """ % (color, n, name + summary, n))
        if 'card' in log[0]:
            for l in log:
                r.append('                    <li class="list-group-item"> %s %s </li>\n' % (l['human_time'], l.get('card_note','bad_card'), ))
        else:
            for l in open_durations(log):
                r.append('                    <li class="list-group-item"> %s was open %s </li>\n' % (l['human_time'], time_dhms(l['open'])))
        r.append("""
                </ul>
            </div>
            """)
    return r

def path(environ):
    p = os.path.join(environ['SCRIPT_NAME'], environ['PATH_INFO'])
    if p == '':
        p = '/'
    return p

def get_recent(source, log_path, count):
    prefix = os.path.join(log_path, source)
    t = lazytable.open(prefix + LOG_DB_SUFFIX, 'log')
    t.index('wall_time')
    c = t.query('SELECT * FROM log ORDER BY wall_time DESC LIMIT ?',[count])
    rows = list(t.fetchall(c))
    return rows

def get_recent_all(log_path, count):
    all = {}
    for f in sorted(os.listdir(log_path)):
        if f.endswith(LOG_DB_SUFFIX):
            source = f.partition(LOG_DB_SUFFIX)[0]
            all[source] = get_recent(source, log_path, count)
    return all

def card_app(environ, start_response):
    if path(environ).endswith('favicon.ico'):
        start_response('404 Not Found', [('Content-type', 'text/plain')])
        return [ '404\n' ]

    (login_ok, headers, output) = check_or_do_login(environ)
    #print (login_ok, headers, output)
    if login_ok:
        # The returned object is going to be printed
        all = get_recent_all(CONFIG['data_path'], 20)
        output = [page_top % ( {'path': path(environ), 
                    'now':time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} ) ] + render_dropdowns(all) + [page_end % ({'path':path(environ)})]
        headers.append(('Content-type', 'text/html'))
    else:
        headers.append(('Content-type', 'text/html'))
    #send response
    status = '200 OK' # HTTP Status
    start_response(status, headers)
    return output

def load_config(cf):
    global CONFIG

    c = ConfigParser.ConfigParser()
    c.readfp(open(cf))
    CONFIG = dict(c.items('web_ui'))

    CONFIG['port'] = int(CONFIG['port'])
    CONFIG['login_time'] = int(CONFIG['login_time'])

    # check config
    error = False
    for k in ('port', 'data_path', 'secret', 'username', 'password_salt', 'hex_hmac_passwd', 'login_time'):
        if k not in CONFIG:
            print '%s not in config' % k
            error = True
    if error:
        exit(1)

class NoDNSWSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def address_string(self):
        host, port = self.client_address[:2]
        return host

class KeepAliveWSGIServer(wsgiref.simple_server.WSGIServer):
    def get_request(self):
        (conn, address) = wsgiref.simple_server.WSGIServer.get_request(self)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 2)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 2)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)
        return (conn, address)

if __name__ == '__main__':
    usage = """%prog web_ui.ini"""
    parser = optparse.OptionParser(usage)
    (options, args) = parser.parse_args()

    load_config(args[0])
    httpd = wsgiref.simple_server.make_server('', CONFIG['port'], card_app, 
                server_class=KeepAliveWSGIServer, handler_class=NoDNSWSGIRequestHandler)
    # Serve until process is killed
    httpd.serve_forever()
    #httpd.handle_request()
