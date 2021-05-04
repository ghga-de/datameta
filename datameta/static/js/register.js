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

'use strict';

//Get usage agreement as well as a list of all groups from a custom endpoint
function getGroupsAndUsageAgreement() {
    fetch(DataMeta.api("registrationsettings"),
    {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function(response) {
        if(response.ok) {
            return response.json()
        }   else {
            throw new Error()
        }
    }).then((json) => {
        populateUserAgreement(json.userAgreement);
        populateGroupSelector(json.groups);
    }).catch((error) => {
        alert("An unknown error occured.");
    });
}

function populateGroupSelector(groups) {
    var orgSelect = document.getElementById("org_select");

    groups.forEach(group => {
        var option = document.createElement('option')
        option.value = group.id.uuid;
        option.innerHTML = group.name;
        orgSelect.appendChild(option)
    })
}

function populateUserAgreement(userAgreement) {

    if(userAgreement) {
        document.getElementById("user_agreement_container").style.display="block";
        document.getElementById("user_agreement").innerHTML = userAgreement;
    } else {
        // Hide Usage Agreement, if it was null or empty (should already be hidden)
        document.getElementById("user_agreement_container").style.display="none";
    }
}

function clearAlert() {
    var elem_alert = document.getElementById("alert")
    elem_alert.style.display="none";
}

window.addEventListener("load", function() {

    getGroupsAndUsageAgreement();

    document.getElementById("regform").addEventListener("submit", function(event) {
        var data = new FormData(event.target);
        var fieldset = document.getElementById("regfieldset");
        fieldset.disabled = true;

        // Prevent form submission
        event.preventDefault();

        var elem_alert = document.getElementById("alert")
        var closeAlertButton = '<button type="button" class="btn-close" id="dismiss_alert" onclick="clearAlert()"></button>'

        fetch(DataMeta.api('registrations'),
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name:                   data.get('name'),
                email:                  data.get('email'),
                org_select:             data.get('org_select'),
                org_create:             data.get('org_create'),
                org_new_name:           data.get('org_new_name'),
                check_user_agreement:   data.get("check_user_agreement") == "on"
            })
        })
        .then((response) => {
            if (response.status === 204) {
                elem_alert.style.display="none"
                document.getElementById("regform").style.display="none"
                document.getElementById("success").style.display="block"
                return;
            } else if(response.status === 400) {
                response.json().then((json) => {
                    var errorFields = json.map(error => error.field);

                    var keys = ["name", "email", "org_select", "org_new_name", "check_user_agreement"];

                    keys.forEach(function(key) {
                        if (errorFields.includes(key)) {
                            document.getElementById(key).classList.remove("is-valid");
                            document.getElementById(key).classList.add("is-invalid");
                        } else {
                            document.getElementById(key).classList.remove("is-invalid");
                            document.getElementById(key).classList.add("is-valid");
                        }
                    });
                    // User exists
                    if (errorFields.includes("user_exists")) {
                        elem_alert.innerHTML = 'This email address is already registered. Please use the <a href="/login">login</a> page. ' + closeAlertButton;
                        document.getElementById("email").classList.remove("is-valid");
                        document.getElementById("email").classList.add("is-invalid");
                        elem_alert.style.display="block";
                    } else if (errorFields.includes("req_exists")) {
                        elem_alert.innerHTML = 'Your request is already being reviewed. You will be contacted shortly. ' + closeAlertButton;
                        elem_alert.style.display="block";
                    }
                    fieldset.disabled = false;
                });
            } else {
                throw new Error();
            }      
        }).catch((error) => {
            elem_alert.innerHTML = 'An unknown error occurred. Please try again later. ' + closeAlertButton;
            elem_alert.style.display="block";
            fieldset.disabled = false;
        });
    });

    document.getElementById("toggle_new_org").addEventListener("change", function(event) {
        var valids = document.getElementsByClassName("is-valid");
        while (valids.length)
            valids[0].classList.remove("is-valid")

        if (event.target.checked) {
            document.getElementById("org_select_div").classList.remove("is-valid", "is-invalid");
            document.getElementById("org_new").classList.remove("is-valid", "is-invalid");
            document.getElementById("org_select_div").style.display = "none";
            document.getElementById("org_new").style.display = "block";
        } else {
            document.getElementById("org_select_div").classList.remove("is-valid", "is-invalid");
            document.getElementById("org_new").classList.remove("is-valid", "is-invalid");
            document.getElementById("org_select_div").style.display = "block";
            document.getElementById("org_new").style.display = "none";
        }
    });

});
