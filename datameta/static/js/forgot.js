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
        new bootstrap.Collapse(document.getElementById("success"), { show: true })
    }

    function show_alert(text) {
        var al = document.getElementById("alert");
        al.innerHTML = text
        new bootstrap.Collapse(al, { show: true })
    }
    document.getElementById("forgotform").addEventListener("submit", function(event) {
        // Prevent form submission
        event.preventDefault();
        var form = event.target;
        var data = new FormData(form);

        var fieldset = document.getElementById("forgotfieldset");
        fieldset.disabled = true;


        document.getElementById("email").classList.remove("is-invalid");
        document.getElementById("success").classList.remove("show");

        fetch('/api/ui/forgot',
            {
                method: 'post',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: data.get("email")
                })
            })
            .then(response => response.json())
            .then(function (json) {
                fieldset.disabled = false;
                if (json.success) {
                    view_success();
                    return;
                } else if (json.error=='MALFORMED_EMAIL') {
                    document.getElementById("email").classList.add("is-invalid");
                } else {
                    show_alert("An unknown error occurred. Please try again.");
                }
            })
            .catch((error) => {
                fieldset.disabled = false;
                show_alert("An unknown error occurred. Please try again.");
                console.log(error);
            });
    });

});
