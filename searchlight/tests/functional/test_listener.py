# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import json
import uuid

from searchlight.tests import functional


MATCH_ALL = {"query": {"match_all": {}}}
IMAGES_EVENTS_FILE = "searchlight/tests/functional/data/events/images.json"
METADEF_EVENTS_FILE = "searchlight/tests/functional/data/events/metadefs.json"

OWNER1 = str(uuid.uuid4())


class StevedoreMock(object):
    """Act like a stevedore-loaded plugin for the sake of the listener code"""
    def __init__(self, plugin):
        self.obj = plugin
        self.name = plugin.document_type


class TestSearchListenerBase(functional.FunctionalTest):

    def __init__(self, *args, **kwargs):
        super(TestSearchListenerBase, self).__init__(*args, **kwargs)
        self.image_events, self.metadef_events = self._load_events()

    def _load_events(self):
        with open(IMAGES_EVENTS_FILE, "r") as file:
            image_events = json.load(file)
        with open(METADEF_EVENTS_FILE, "r") as file:
            metadef_events = json.load(file)
        return image_events, metadef_events

    def _send_event_to_listener(self, event):
        event = copy.deepcopy(event)
        self.notification_endpoint.info(
            event['ctxt'],
            event['publisher_id'],
            event['event_type'],
            event['payload'],
            event['metadata']
        )
        self._flush_elasticsearch(self.images_plugin.get_index_name())
        self._flush_elasticsearch(self.metadefs_plugin.get_index_name())

    def _verify_event_processing(self, event, count=1, owner=None):
        if not owner:
            owner = event['payload']['owner']
        response, json_content = self._search_request(
            MATCH_ALL,
            owner, role="admin")
        self.assertEqual(count, json_content['hits']['total'])
        return json_content

    def _verify_result(self, event, verification_keys, result_json):
        input = event['payload']
        result = result_json['hits']['hits'][0]['_source']
        for key in verification_keys:
            self.assertEqual(input[key], result[key])
