#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# vim:syntax=python:sw=4:ts=4:expandtab
#

import couchdbkit as couch
import logging,urlparse,sys,datetime
import json,yaml

# Configure Logs
log = logging.getLogger('vogeler-server')

# Correct problem with urlparse in python < 2.6
SCHEME="couch"
urlparse.uses_netloc.append(SCHEME)
urlparse.uses_fragment.append(SCHEME)

class SystemRecord(couch.Document):
    """
    A couchdbkit document for storing our base information
    All documents, regardless of backend, should support the following fields:
    system_name
    created_at
    updated_at
    """
    system_name = couch.StringProperty()
    created_at = couch.DateTimeProperty()
    updated_at = couch.DateTimeProperty()


class Store(object):
    def __init__(self, config):
        """ ParseResult(scheme='couch', netloc='1.2.3.4:5984', path='/toto', params='', query='', fragment='')
        @NOTE: The reason we use a dsn_couchdb and not directly the dsn variable
        is because we want to later factor the Store class to be generic and call
        the good backend plugin, so we'll have couch, mongo, etc.
        """
        dsn = config.get('main','storeserver')
        result = urlparse.urlparse(dsn)
        dsn_couchdb = 'http://'+result.netloc

        log.info('Initializing connection to database %s' % dsn_couchdb)
        self._server = couch.Server(uri=dsn_couchdb)
        self.db = self._server.get_or_create_db(result.path[1:])
        SystemRecord.set_db(self.db)
        log.info("Established CouchDB connection to %s" % dsn_couchdb)

    def get(self, node_name):
        """ Retrieves a node_name, return None if does not exist """
        try:
            node = SystemRecord.get(node_name)
        except couch.resource.ResourceNotFound:
            return None
        return node

    def create(self,node_name):
        # @TODO: Not good, go inside each time then updates the created_at
        log.debug("Doing db.create(%s)" % node_name)
        node = SystemRecord.get_or_create(node_name)
        node['system_name'] = node_name
        node['created_at'] = datetime.datetime.utcnow()
        node.save()

    def update(self, node_name, key, value, message_format):
        log.debug("Doing db.update(%s, %s, xxx, %s)" % (node_name,key,message_format))
        # @TODO: IMPLEMENT MESSAGEFORMAT
        node = SystemRecord.get_or_create(node_name)

        try:
            datatype_method = getattr(self, '_update_%s' % message_format)
            data = datatype_method(node_name, key, value)
        except AttributeError:
            log.warn("Don't know how to handle datatype: '%r'" % message_format)

        node[key] = data
        node['updated_at'] = datetime.datetime.utcnow()
        node.save()

    def _update_yaml(self, node, key, value):
        return yaml.load(value)

    def _update_pylist(self, node, key, value):
        return value

    def _update_pydict(self, node, key, value):
        return value

    def _update_json(self, node, key, value):
        return json.loads(value)

    def _update_raw(self, node, key, value):
        return value

    def _update_string(self, node, key, value):
        return value


if __name__ == '__main__':
    store = Store()
