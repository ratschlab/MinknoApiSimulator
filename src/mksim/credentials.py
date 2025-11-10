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

from os.path import dirname, join

PROJECT_ROOT = dirname(dirname(dirname(__file__)))
CERT_DIR = PROJECT_ROOT + "/certs/"
CLIENT_CERT_FILE = CERT_DIR + "client.pem"
CLIENT_KEY_FILE = CERT_DIR + "client.key"
SERVER_CERT_FILE = CERT_DIR + "server.pem"
SERVER_KEY_FILE = CERT_DIR + "server.key"

def load_credential_from_file(filepath, binary=True):
    # real_path = os.path.join(os.path.dirname(__file__), filepath)
    mode = 'rb' if binary else 'r'
    with open(filepath, mode) as f:
        return f.read()
