/*
# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
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

        // Validation
        var data = new FormData(form);

        if (data.get("new_password") != data.get("new_password_repeat")) {
            document.getElementById("new_password_repeat").classList.add("is-invalid")
            return;
        } else {
            document.getElementById("new_password_repeat").classList.remove("is-invalid")
        }

        // Talk to the API
        fetch(DataMeta.api("users/0/password"),
            {
                method: 'PUT',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    passwordChangeCredential: form.getAttribute("data-datameta-setpass"),
                    newPassword: data.get("new_password")
                })
            })
            .then(function(response) {
                console.log("response", response);
                if (response.status==404) { // HTTPNotFound - Unknown token
                    window.location.replace("/login");
                } else if (response.status==400) {
                    throw new DataMeta.AnnotatedError(response);
                } else if (response.status==410) { // HTTPGone - Expired
                    // Reload the page so that a new token is triggered. This
                    // covers only the case where the token expires while the
                    // user enters a new password. If the token was already
                    // expired when the user entered the page, the backend
                    // handles generating and sending a new token.
                    window.location.replace("/setpass/" + form.getAttribute("data-datameta-setpass"))
                } else if (response.ok) {
                    response.json().then(function (body) {
                        if (body["tfaToken"] === "") {
                            view_success();
                        } else {
                           window.location.replace("/settfa/" + body["tfaToken"])
                        }
                    });
                    return;
                } else {
                    console.log("unknown response status from /users/0/password", response);
                    throw new Error();
                }
            }).catch((error) => {
                if (error instanceof DataMeta.AnnotatedError) {
                    error.response.json().then(function(json){
                        show_alert(json[0].message);
                    });
                } else {
                    show_alert("An unknown error occurred. Please try again.");
                    console.log(error);
                }
            });
    });
});
