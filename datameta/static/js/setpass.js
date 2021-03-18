/*
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
*/

window.addEventListener("load", function() {

    function view_success() {
        new bootstrap.Collapse(document.getElementById("passentry"), { hide: true })
        new bootstrap.Collapse(document.getElementById("success"), { show: true })
    }

    function show_alert(text) {
        var al = document.getElementById("alert");
        al.innerHTML = text
        new bootstrap.Collapse(al, { show: true })
    }

    document.getElementById("newpassform").addEventListener("submit", function(event) {
        // Prevent form submission
        event.preventDefault();

        document.getElementById("alert").classList.remove("show");

        var form = event.target

        // Validataion
        var data = new FormData(form);

        if (data.get("new_password") != data.get("new_password_repeat")) {
            document.getElementById("new_password_repeat").classList.add("is-invalid")
            return;
        } else {
            document.getElementById("new_password_repeat").classList.remove("is-invalid")
        }

        // Talk to the API
        fetch('/api/setpass',
            {
                method: 'post',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: form.getAttribute("data-datameta-setpass"),
                    new_password: data.get("new_password")
                })
            })
            .then(response => response.json())
            .then(function (json) {
                if (json.success) {
                    view_success();
                    return;
                } else if (json.error == "TOKEN_NOT_FOUND") {
                    window.location.replace("/login");
                } else if (json.error == "TOKEN_EXPIRED") {
                    // Refresh page so that a new token is triggered
                    window.location.replace("/setpass/" + form.getAttribute("data-datameta-setpass"))
                } else if (json.error == "CUSTOM") {
                    show_alert(json.error_msg);
                }
            })
            .catch((error) => {
                show_alert("An unknown error occurred. Please try again later.");
                console.log(error);
            });
    });
});
