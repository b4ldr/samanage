#!/usr/bin/env python

import json
import urllib
import logging
import argparse
import requests

class Record(object):
    def __init__(self, json_payload):
        self.id   = json_payload.get('id', None)
        self.name = json_payload.get('name', None)

    def __str__(self):
        return u'{}\n\t'.format(self.name) + '\n\t'.join([u'{}: {}'.format(k,v) 
            for k,v in self.__dict__.items() if v])

    def json(self):
        return json.dumps(self, 
                default=lambda o: {k: v for k,v in o.__dict__.items() if v})

class CatalogItems(Record):
    pass

class User(Record):
    pass

class Department(Record):
    pass

class Hardware(Record):
    def __init__(self, json_payload):
        super(Hardware, self).__init__(json_payload)
        self.bio               = [{'ssn': ''}]
        self.address           = json_payload.get('address', '')
        self.asset_tag         = json_payload.get('asset_tag', '')
        self.category          = json_payload.get('category', '')
        self.department        = json_payload.get('department', '')
        self.description       = json_payload.get('description', '')
        self.domain            = json_payload.get('domain', '')
        self.ip                = json_payload.get('ip', '')
        self.latitude          = json_payload.get('latitude', '')
        self.longitude         = json_payload.get('longitude', '')
        self.networks          = json_payload.get('networks', '')
        self.notes             = json_payload.get('notes', '')
        self.owner             = json_payload.get('owner', '')
        self.status            = json_payload.get('status', '')
        self.technical_contact = json_payload.get('technical_contact', '')
        self.username          = json_payload.get('username', '')

    def __repr__(self):
        return 'Hardware()'

class Samanage(object):

    supported_types = {
            'hardwares': Hardware,
            'users': User,
            'departments': Department,
            'catalog_items': CatalogItems,
            }

    def __init__(self, username, password, uri):
        self.username     = username
        self.password     = password
        self.uri          = uri
        self.logger       = logging.getLogger('samanage.Samanage')
        self.session      = requests.Session()
        self.session.auth = requests.auth.HTTPDigestAuth(
                self.username, self.password)
        self.logger.debug('using credentials: {}/{}'.format(
            self.username, self.password))

    def _uri(self, record_type, record_id=None):
        if record_type not in self.supported_types:
            raise ValueError('{} not supported'.format(record_type))

        if record_id:
            uri = '{}/{}/{}.json'.format(self.uri, record_type, record_id) 
        else:
            uri = '{}/{}.json'.format(self.uri, record_type) 
        return uri

    def _get_uri(self, record_type, count=25, record_id=None, search={}):
        '''build the uri with correct parameters'''
        uri = self._uri(record_type, record_id)
        search['per_page'] = count
        if search:
            self.logger.debug('add search paramter: {}'.format(search))
            uri += '?{}'.format(urllib.urlencode(search))

        self.logger.debug('fetching uri:{}'.format(uri))    
        return uri

    def get(self, record_type, count=25, record_id=None, search={}):
        results = []
        headers = {'Accept' : 'application/vnd.samanage.v1.2+json'}
        uri = self._get_uri(record_type, count, record_id, search)
        request = self.session.get(uri, headers=headers)
        if request.status_code >  201:
            self.logger.error('HTTP {}:{}'.format(
                request.status_code, request.text))
            return
        else:
            json_out = request.json()
            self.logger.debug(json.dumps(json_out, indent=4))
            self.logger.debug('Response Headers: {}'.format(request.headers))
            if type(json_out) is list:
                for record in json_out:
                    results.append(
                            self.supported_types.get(record_type, Record)(record))
            else:
                results.append(
                        self.supported_types.get(record_type, Record)(json))
            return results

    def post(self, record_type, payload, record_id=None):
        headers = { 
                'Accept'       : 'application/vnd.samanage.v1.2+json',
                'Content-Type' : 'text/json',
                }
        uri = self._uri(record_type, record_id)
        request = self.session.post(uri, payload, headers=headers)
        

def main():
    parser = argparse.ArgumentParser(description='dns spoof monitoring script')
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-T', '--type', required=True)
    parser.add_argument('-I', '--id', default=None)
    parser.add_argument('-U', '--uri', default='https://api.samanage.com',
            help='Sammanage api hendpoint')
    parser.add_argument('-S', '--search', default='{}', type=json.loads, 
            help='Search parameters as a hash')
    parser.add_argument('-C', '--count', default=25, 
            help='Number of entries to return')
    parser.add_argument('-v','--verbose', action="count")
    args = parser.parse_args()

    log_level = logging.ERROR
    if args.verbose == 1:
        log_level = logging.WARN
    elif args.verbose == 2:
        log_level = logging.INFO
    elif args.verbose > 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    logger = logging.getLogger('samanage.main')

    client = Samanage(args.username, args.password, args.uri)
    results = client.get(args.type, args.count, args.id, args.search)
    if results:
        for result in results:
            print u'{}'.format(result)


if __name__ == '__main__':
    main()
