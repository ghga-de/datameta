# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('root', '/')
    config.add_route('login', '/login')
    config.add_route('register', '/register')
    config.add_route('register_submit', '/register/submit')
    config.add_route('setpass', '/setpass/{token}')
    config.add_route('forgot', '/forgot')
    config.add_route('forgot_api', '/api/forgot')
    config.add_route('home', '/home')
    config.add_route('submit', '/submit')
    config.add_route('submit_action', '/submit/action')
    config.add_route('account', '/account')
    config.add_route('view', '/view')
    config.add_route('v_submit_view_json', '/submit/view.json')
    # ADMIN
    config.add_route('admin', '/admin')
    config.add_route('admin_get', '/api/admin')
    config.add_route('admin_put_request', '/api/admin/request')
