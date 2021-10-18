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

    function view_2fa_success() {
        new bootstrap.Collapse(document.getElementById("tfa_qrcode"), { hide: true })
        new bootstrap.Collapse(document.getElementById("success"), { show: true })
    }

    function hide_qrcode() {
        new bootstrap.Collapse(document.getElementById("tfa_qrcode"), { hide: true})
    }

    function show_alert(text) {
        var al = document.getElementById("alert");
        al.innerHTML = text
        new bootstrap.Collapse(al, { show: true })
    }

    if (this.document.getElementById("otp_setup_form")) {

    this.document.getElementById("otp_setup_form").addEventListener("submit", function(event) {
        // Prevent form submission
        event.preventDefault();

        document.getElementById("alert").classList.remove("show");

        var form = event.target

        // Validation
        var data = new FormData(form);

        fetch(
            "/api/ui/set_otp",
            {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: form.getAttribute("data-datameta-tfa"),
                    inputOTP: data.get("input_otp")
                })
            }
        ).then(function(response) {
            console.log("response", response);
            if (response.status==400) {
                throw new DataMeta.AnnotatedError(response);
            } else if (response.status==410) {
                //document.getElementById("tfa_qrcode").classList.remove("show");
                hide_qrcode(); // why does this not hide???

                throw new DataMeta.AnnotatedError("'The 2fa setup session has expired. Please reset your password.'")
                //window.location.replace("/login");
            }else if (response.ok) {
                view_2fa_success();
            } else if (response.status == 404) {
                // document.getElementById("input_otp").classList.add("is-invalid")
                window.location.replace("/login");

            }
            return;
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
    }

});
