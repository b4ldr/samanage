#!/usr/bin/env python

import json
import logging
import argparse
import requests

class Record(object):
    def __init__(self, json_payload):
        self.id   = json_payload.get('id', None)
        self.name = json_payload.get('name', None)

    def __str__(self):
        return u'{} - {}'.format(self.id, self.name)

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class Hardware(Record):

    def __init__(self, json_payload):
        super(Hardware, self).__init__(json_payload)
        self.address           = json_payload.get('address', None)
        self.asset_tag         = json_payload.get('asset_tag', None)
        self.category          = json_payload.get('category', None)
        self.department        = json_payload.get('department', None)
        self.description       = json_payload.get('description', None)
        self.domain            = json_payload.get('domain', None)
        self.ip                = json_payload.get('ip', None)
        self.latitude          = json_payload.get('latitude', None)
        self.longitude         = json_payload.get('longitude', None)
        self.networks          = json_payload.get('networks', None)
        self.notes             = json_payload.get('notes', None)
        self.owner             = json_payload.get('owner', None)
        self.status            = json_payload.get('status', None)
        self.technical_contact = json_payload.get('technical_contact', None)
        self.username          = json_payload.get('username', None)

    def __repr__(self):
        return 'Hardware()'

class Samanage(object):

    supported_types = {'hardwares': Hardware}

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

    def get(self, record_type, record_id=None):
        results = []
        if record_type not in self.supported_types:
            raise ValueError('{} not supported'.format(record_type))
        headers = {'Accept' : 'application/vnd.samanage.v1.2+json'}
        if record_id:
            uri     = '{}/{}/{}.json'.format(self.uri, record_type, record_id) 
        else:
            uri     = '{}/{}.json'.format(self.uri, record_type) 
        self.logger.debug('fetching uri:{}'.format(uri))    
        request = self.session.get(uri, headers=headers)
        if request.status_code >  201:
            self.logger.error('HTTP {}:{}'.format(
                request.status_code, request.text))
            return
        else:
            json_out = request.json()
            self.logger.debug(json.dumps(json_out, indent=4))
            if type(json_out) is list:
                for record in json_out:
                    results.append(
                            self.supported_types.get(record_type, Record)(record))
            else:
                results.append(
                        self.supported_types.get(record_type, Record)(json))
            return results



def main():
    parser = argparse.ArgumentParser(description='dns spoof monitoring script')
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-T', '--type', required=True)
    parser.add_argument('-I', '--id', default=None)
    parser.add_argument('-U', '--uri', default='https://api.samanage.com',
            help='Sammanage api hendpoint')
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
    results = client.get(args.type, args.id)
    if results:
        for result in results:
            print u'{}'.format(result.json())


if __name__ == '__main__':
    main()
