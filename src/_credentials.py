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


def _load_credential_from_file(filepath, binary=True):
    real_path = os.path.join(os.path.dirname(__file__), filepath)
    mode = 'rb' if binary else 'r'
    with open(real_path, mode) as f:
        return f.read()

CERTS_DIR = "/home/sayan/Downloads/readuntil_fake/python_readuntil_client/generate_certs/generated"


SERVER_CERTIFICATE = _load_credential_from_file(CERTS_DIR + "server.crt")
SERVER_CERTIFICATE_KEY = _load_credential_from_file(CERTS_DIR + "server.key")
ROOT_CERTIFICATE = _load_credential_from_file(CERTS_DIR + "ca.crt")
DEV_API_TOKEN = _load_credential_from_file("/home/sayan/Documents/minknow-api-token.txt", binary=False)