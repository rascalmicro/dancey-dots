#!./uwsgi --http-socket :9090 --gevent 100 --module tests.websockets_chat --gevent-monkey-patch
import uwsgi
import time
import gevent.select
import redis

def application(env, sr):

    ws_scheme = 'ws'
    if 'HTTPS' in env or env['wsgi.url_scheme'] == 'https':
        ws_scheme = 'wss'

    if env['PATH_INFO'] == '/':
        sr('200 OK', [('Content-Type','text/html')])
        return """
    <!DOCTYPE html>
<!-- paulirish.com/2008/conditional-stylesheets-vs-css-hacks-answer-neither/ -->
<!-- Consider specifying the language of your content by adding the `lang` attribute to <html> -->
  <!--[if lt IE 7]> <html class="no-js lt-ie9 lt-ie8 lt-ie7"> <![endif]-->
    <!--[if IE 7]>    <html class="no-js lt-ie9 lt-ie8"> <![endif]-->
      <!--[if IE 8]>    <html class="no-js lt-ie9"> <![endif]-->
        <!--[if gt IE 8]><!--> <html class="no-js"> <!--<![endif]-->
          <head>
            <!--
            hey all! i made this as a prototype thinking of collective instruments and
            real time web interactivity.

            A couple days ago I started playing with the web audio api, so this is
            pretty minimal.  I'm putting this out to see how people feel playing with it,
            and how it fares scaling up.  It was built with socketio and node.

            let me know what you think tweet me at @whichlight, or whichlight at gmail dot com

            see other projects at http://whichlight.com/

            -->

            <meta charset="utf-8">

            <title>dancey dots</title>
            <meta name="description" content="">
            <!-- Mobile viewport optimized: h5bp.com/viewport -->
            <meta name="viewport" content="width=device-width">
            <style type="text/css">
              #container{
                font-family:helvetica;
                margin: 0px auto;
                width:650px;
              }

              .synth{
                background-color:pink;
                position: absolute;
                height: 40px;
                min-width: 40px;
                border-radius:20px;
                z-index:-1;
              }
              #info{
                position: absolute;
                right: 10px;
                bottom: 10px;
                z-index: 2;
                padding: 16px 24px;
                color:grey;
                font-size:15px;
                font-family: helvetica;

              }

              #fun{
                position:absolute;
                width:100%;
                height:100%;
              }
            </style>
           </head>
           <body>

             <div id="fun">
               <div id="info">dancey dots by <a href="http://www.whichlight.com">whichlight</a></div>
             </div>
             <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js"></script>
             <script type="text/javascript" src="bower_components/hammerjs/hammer.min.js"></script>
             <script type="text/javascript" src="main.js"></script>
           </body>
         </html>
        """
    elif env['PATH_INFO'] == '/favicon.ico':
        return ""
    elif env['PATH_INFO'] == '/foobar/':
	uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))
        print "websockets..."
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        channel = r.pubsub()
        channel.subscribe('foobar')

        websocket_fd = uwsgi.connection_fd()
        redis_fd = channel.connection._sock.fileno()
        
        while True:
            # wait max 4 seconds to allow ping to be sent
            ready = gevent.select.select([websocket_fd, redis_fd], [], [], 4.0)
            # send ping on timeout
            if not ready[0]:
                uwsgi.websocket_recv_nb()
            for fd in ready[0]:
                if fd == websocket_fd:
                    msg = uwsgi.websocket_recv_nb()
                    if msg:
                        r.publish('foobar', msg)
                elif fd == redis_fd:
                    msg = channel.parse_response() 
                    # only interested in user messages
                    if msg[0] == 'message':
                        uwsgi.websocket_send("[%s] %s" % (time.time(), msg))
