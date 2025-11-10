# Copyright 2019 The gRPC Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Loading SSL credentials for gRPC Python authentication example."""

import os
from os.path import dirname

class Credentials:
    certs_dir = None
    client_cert_file = None
    client_key_file = None
    server_cert_file = None
    server_key_file = None

    @staticmethod
    def load(certs_dir = None):
        if certs_dir is None:
            certs_dir = dirname(dirname(dirname(__file__)))
        Credentials.certs_dir = certs_dir
        Credentials.client_cert_file = os.path.join(certs_dir, "client.pem")
        Credentials.client_key_file = os.path.join(certs_dir, "client.key")
        Credentials.server_cert_file = os.path.join(certs_dir, "server.pem")
        Credentials.server_key_file = os.path.join(certs_dir, "server.key")

    @staticmethod
    def client_key():
        return Credentials._load_credential_from_file(Credentials.client_key_file)

    @staticmethod
    def server_key():
        return Credentials._load_credential_from_file(Credentials.server_key_file)

    @staticmethod
    def client_cert():
        return Credentials._load_credential_from_file(Credentials.client_cert_file)

    @staticmethod
    def server_cert():
        return Credentials._load_credential_from_file(Credentials.server_cert_file)

    @staticmethod
    def _load_credential_from_file(filepath, binary=True):
        # real_path = os.path.join(os.path.dirname(__file__), filepath)
        mode = 'rb' if binary else 'r'
        with open(filepath, mode) as f:
            return f.read()
