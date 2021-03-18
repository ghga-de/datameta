# Copyright 2021 Universität Tübingen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('root', '/')
    config.add_route('login', '/login')
    config.add_route('register', '/register')
    config.add_route('register_submit', '/register/submit')
    config.add_route('setpass', '/setpass/{token}')
    config.add_route('setpass_api', '/api/setpass')
    config.add_route('forgot', '/forgot')
    config.add_route('forgot_api', '/api/forgot')
    config.add_route('home', '/home')
    config.add_route('submit', '/submit')
    config.add_route('account', '/account')
    config.add_route('view', '/view')
    # ADMIN
    config.add_route('admin', '/admin')
    config.add_route('admin_get', '/api/admin')
    config.add_route('admin_put_request', '/api/admin/request')
