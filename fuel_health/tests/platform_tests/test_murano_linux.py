# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import uuid

from fuel_health import muranomanager

from fuel_health.common.utils.data_utils import rand_name


LOG = logging.getLogger(__name__)


class MuranoDeployLinuxServicesTests(muranomanager.MuranoTest):
    """TestClass contains verifications of full Murano functionality.

    Special requirements:
        1. Murano component should be installed.
        2. Internet access for virtual machines in OpenStack.
        3. Linux image with Murano metadata should be imported.
    """

    def setUp(self):
        super(MuranoDeployLinuxServicesTests, self).setUp()
        self.check_clients_state()

        doc_link = ('http://docs.mirantis.com/openstack/fuel/'
                    'fuel-{0}/user-guide.html#platform-tests-'
                    'description'.format(self.config.fuel.fuel_version))

        max_free_ram_mb = (
            self.get_max_free_compute_node_ram(self.min_required_ram_mb))
        if max_free_ram_mb < self.min_required_ram_mb:
            msg = ('This test requires more hardware resources of your '
                   'OpenStack cluster: at least one of the compute nodes '
                   'must have >= {0} MB of free RAM, but you have only '
                   '{1} MB on most appropriate compute node.'
                   .format(self.min_required_ram_mb, max_free_ram_mb))
            LOG.debug(msg)
            self.skipTest(msg)

        self.image = self.find_murano_image('linux')
        if not self.image:
            msg = ('Murano image was not properly registered or was not '
                   'uploaded at all. Please refer to the Mirantis OpenStack '
                   'documentation ({0}) to find out how to upload and/or '
                   'register image for Murano.'.format(doc_link))
            LOG.debug(msg)
            self.skipTest(msg)

        self.flavor_name = rand_name("ostf_test_Murano_flavor")
        self.flavor = self.compute_client.flavors.create(
            self.flavor_name, disk=60, ram=self.min_required_ram, vcpus=1)

    def tearDown(self):
        if self.flavor_reqs:
            self.compute_client.flavors.delete(self.flavor.id)

        super(MuranoDeployLinuxServicesTests, self).tearDown()

    def test_deploy_apache_service(self):
        """Check that user can deploy Apache service in Murano environment
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create Linux-based service Apache.
            4. Request to deploy session.
            5. Checking environment status.
            6. Checking deployments status
            7. Checking ports
            8. Send request to delete environment.

        Duration: 2140 s.

        Deployment tags: Murano, Heat
        """

        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment['id'])

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "Apache"
                },
                "type": "io.murano.apps.apache.ApacheHttpServer",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service. "
        self.verify(5, self.create_service,
                    3, fail_msg, "service creating",
                    self.environment['id'], session['id'], post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    4, fail_msg,
                    "sending session on deployment",
                    self.environment['id'], session['id'])

        fail_msg = "Deployment was not completed correctly. "
        environment = self.verify(1800, self.deploy_check,
                                  5, fail_msg, 'deployment is going',
                                  self.environment['id'])

        self.verify(5, self.deployments_status_check,
                    6, fail_msg,
                    'Check deployments status',
                    self.environment['id'])

        self.verify(300, self.ports_check,
                    7, fail_msg,
                    'Check that needed ports are opened',
                    environment, ['80'])

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    8, fail_msg, "deleting environment",
                    self.environment['id'])

    def test_deploy_wordpress_app(self):
        """Check that user can deploy WordPress app in Murano environment
        Target component: Murano

        Scenario:
            1. Send request to create environment.
            2. Send request to create session for environment.
            3. Send request to create Linux-based service Apache.
            4. Send request to create MySQL.
            5. Send request to create WordPress.
            6. Request to deploy session.
            7. Checking environment status.
            8. Checking deployments status.
            9. Checking WordPress path.
            10. Send request to delete environment.

        Duration: 2140 s.

        Deployment tags: Murano, Heat
        """
        fail_msg = "Can't create environment. Murano API is not available. "
        self.environment = self.verify(15, self.create_environment,
                                       1, fail_msg, 'creating environment',
                                       self.env_name)

        fail_msg = "User can't create session for environment. "
        session = self.verify(5, self.create_session,
                              2, fail_msg, "session creating",
                              self.environment['id'])

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "enablePHP": True,
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "Apache"
                },
                "type": "io.murano.apps.apache.ApacheHttpServer",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service Apache. "
        self.apache = self.verify(5, self.create_service,
                                  3, fail_msg, "service creating",
                                  self.environment['id'], session['id'],
                                  post_body)

        post_body = {
            "instance": {
                "flavor": self.flavor_name,
                "image": self.image.name,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": rand_name("testMurano")
            },
            "name": rand_name("teMurano"),
            "database": rand_name("ostf"),
            "username": rand_name("ostf"),
            "password": rand_name("Ost1@"),
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "MySQL"
                },
                "type": "io.murano.databases.MySql",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service MySQL. "
        self.mysql = self.verify(5, self.create_service,
                                 4, fail_msg, "service creating",
                                 self.environment['id'], session['id'],
                                 post_body)

        post_body = {
            "name": rand_name("teMurano"),
            "server": self.apache,
            "database": self.mysql,
            "dbName": "wordpress",
            "dbUser": "wp_user",
            "dbPassword": "U0yleh@c",
            "?": {
                "_{id}".format(id=uuid.uuid4().hex): {
                    "name": "WordPress"
                },
                "type": "io.murano.apps.WordPress",
                "id": str(uuid.uuid4())
            }
        }

        fail_msg = "User can't create service WordPress. "
        self.verify(5, self.create_service,
                    5, fail_msg, "service creating",
                    self.environment['id'], session['id'], post_body)

        fail_msg = "User can't deploy session. "
        self.verify(5, self.deploy_session,
                    6, fail_msg,
                    "sending session on deployment",
                    self.environment['id'], session['id'])

        fail_msg = "Deployment was not completed correctly. "
        environment = self.verify(1800, self.deploy_check,
                                  7, fail_msg, 'deployment is going',
                                  self.environment['id'])

        self.verify(5, self.deployments_status_check,
                    8, fail_msg,
                    'Check deployments status',
                    self.environment['id'])

        fail_msg = "Path to WordPress unavailable"
        self.verify(10, self.check_path, 9, fail_msg,
                    'checking path availability', environment, "wordpress")

        fail_msg = "Can't delete environment. "
        self.verify(5, self.delete_environment,
                    10, fail_msg, "deleting environment",
                    self.environment['id'])
