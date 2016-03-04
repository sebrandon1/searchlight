# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
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

from searchlight.elasticsearch.plugins import base
from searchlight.elasticsearch.plugins.neutron import notification_handlers
from searchlight.elasticsearch.plugins.neutron import serialize_port
from searchlight.elasticsearch.plugins import openstack_clients


class PortIndex(base.IndexBase):
    NotificationHandlerCls = notification_handlers.PortHandler

    ADMIN_ONLY_FIELDS = ["binding:*"]

    @classmethod
    def get_document_type(self):
        return 'OS::Neutron::Port'

    @classmethod
    def parent_plugin_type(cls):
        return 'OS::Neutron::Net'

    def get_parent_id_field(self):
        return 'network_id'

    def get_mapping(self):
        string_not_analyzed = {'type': 'string', 'index': 'not_analyzed'}
        ordered_string = {'type': 'string',
                          'fields': {'raw': string_not_analyzed}}

        # TODO(sjmc7): denormalize 'device' fields (instance_id, router_id)?
        return {
            'dynamic': True,
            'properties': {
                'admin_state_up': {'type': 'boolean'},
                'binding:host_id': string_not_analyzed,
                # device_owner and device_id identifies e.g which router
                # or instance 'owns' a port
                'device_id': string_not_analyzed,
                'device_owner': string_not_analyzed,
                'id': string_not_analyzed,
                'mac_address': string_not_analyzed,
                'name': ordered_string,
                'network_id': string_not_analyzed,
                'tenant_id': string_not_analyzed,
                'status': {'type': 'string'},
                'fixed_ips': {
                    'type': 'nested',
                    'properties': {
                        'subnet_id': string_not_analyzed,
                        'ip_address': string_not_analyzed
                    }
                },
                # Unfortunately this doesn't come from neutron
                'updated_at': {'type': 'string', 'index': 'not_analyzed'}
            }
        }

    @property
    def admin_only_fields(self):
        from_conf = super(PortIndex, self).admin_only_fields
        return from_conf + PortIndex.ADMIN_ONLY_FIELDS

    def _get_rbac_field_filters(self, request_context):
        return [
            {'term': {'tenant_id': request_context.owner}}
        ]

    def get_objects(self):
        neutron_client = openstack_clients.get_neutronclient()
        for port in neutron_client.list_ports()['ports']:
            yield port

    def serialize(self, port):
        return serialize_port(port)