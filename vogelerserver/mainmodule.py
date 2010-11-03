# -*- coding: utf-8 -*-
# vim:syntax=python:sw=4:ts=4:expandtab
#

from vogelerserver import __version__ as version
from vogelerserver import store_couchdb as store
from amqplib import client_0_8 as amqp
import urlparse,logging,sys,time

# Configure Logs
log = logging.getLogger('vogeler-server')

# Correct problem with urlparse in python < 2.6
SCHEME="amqp"
urlparse.uses_netloc.append(SCHEME)
urlparse.uses_fragment.append(SCHEME)

try:
    import simplejson as json
except ImportError:
    import json

class Manager:
    def __init__(self, config):
        self.config = config
        self.ch = None
        self.queue = self.config.get('main', 'server_queue')
        self.setup_amqp_server()
        self.db = store.Store(self.config)

    def setup_amqp(self):
        """ Setup and return a channel """
        dsn = self.config.get('main', 'amqpserver')

        parsed = urlparse.urlparse(dsn)
        u,p,h,pt,vh = (parsed.username, parsed.password, parsed.hostname,
                       parsed.port, parsed.path)

        log.debug('Will connect to AMQP server at %s', dsn)
        try:
            conn = amqp.Connection(host=h, port=pt,
                                   userid=u, password=p,
                                   virtual_host=vh,
                                   insist=False)
            ch = conn.channel()
            ch.access_request(vh, active=True, read=True, write=True)
        except Exception,e:
            log.fatal('Unable to connect to amqp: %s' % e)
            sys.exit(1)

        return ch

    def setup_amqp_server(self):
        """ Setup a client AMQP binding """
        master_exchange = self.config.get('main', 'master_exchange')
        broadcast_exchange = self.config.get('main', 'broadcast_exchange')

        ch = self.setup_amqp()

        try:
            # broadcast exchange for clients to receive messages
            log.debug('Creating Exchange %s' % broadcast_exchange)
            ch.exchange_declare(broadcast_exchange, 'topic', durable=True, auto_delete=False)
            # direct exchange for server to get messages from clients
            log.debug('Creating Exchange %s' % master_exchange)
            ch.exchange_declare(master_exchange, 'direct', durable=True, auto_delete=False)
            # Now our own queues
            log.debug('Creating Queue %s' % self.queue)
            ch.queue_declare(self.queue, durable=True, auto_delete=False)
            # And then we bind to our channel
            log.debug('Binding Queue %s to Exchange %s' % (self.queue,master_exchange))
            ch.queue_bind(self.queue, master_exchange)
        except Exception,e:
            log.fatal('Unable to setup amqp queues: %s' % e)
            sys.exit(1)

        self.ch = ch


    def process_message(self, message):
        try:
            response = message
            syskey = message['syskey']
            message_format = message['format']
            del message['syskey']
            del message['format']

            log.info("Incoming message from: %s" % syskey)

            if not self.db.get(syskey):
                self.db.create(syskey)

            for k, v in response.iteritems():
                try:
                    self.db.update(syskey, k, v, message_format)
                except Exception, e:
                    log.error("Error in updating database: %s" % e)

        except TypeError,e:
            log.error("Invalid message: %s. Discarding" % message)

    def callback(self,msg):
        log.debug('Message received')
        try:
            message = json.loads(msg.body)
        except Exception,e:
            log.error("Message not in JSON format: %s", message)

        self.process_message(message)

    def monitor(self):
        self.ch.basic_consume(self.queue, callback=self.callback, no_ack=True)
        while self.ch.callbacks:
            self.ch.wait()

def main(config, infos, args):
    print "vogelerserver version",version

    m = Manager(config)
    m.monitor()
