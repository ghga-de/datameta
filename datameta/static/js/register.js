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
    fetch(DataMeta.api("register/groups_and_agreement"),
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

window.addEventListener("load", function() {
    getGroupsAndUsageAgreement();

    document.getElementById("regform").addEventListener("submit", function(event) {
        var data = new FormData(event.target);
        var fieldset = document.getElementById("regfieldset");
        fieldset.disabled = true;

        // Prevent form submission
        event.preventDefault();

        var xhr = new XMLHttpRequest();

        xhr.onreadystatechange = function(){
            elem_alert = document.getElementById("alert")
            if (xhr.readyState === 4){
                if (xhr.status === 200) {
                    var json = JSON.parse(xhr.responseText);
                    if (json.success) {
                        elem_alert.style.display="none"
                        document.getElementById("regform").style.display="none"
                        document.getElementById("success").style.display="block"
                    } else {
                        var keys = ["name", "email", "org_select", "org_new_name", "check_user_agreement"];

                        keys.forEach(function(key) {
                            if (key in json.errors) {
                                document.getElementById(key).classList.remove("is-valid");
                                document.getElementById(key).classList.add("is-invalid");
                            } else {
                                document.getElementById(key).classList.remove("is-invalid");
                                document.getElementById(key).classList.add("is-valid");
                            }
                        });
                        // User exists
                        if ("user_exists" in json.errors) {
                            elem_alert.innerHTML = 'This email address is already registered. Please use the <a href="/login">login</a> page.';
                            elem_alert.style.display="block";
                        } else if ("req_exists" in json.errors) {
                            elem_alert.innerHTML = 'Your request is already being reviewed. You will be contacted shortly.';
                            elem_alert.style.display="block";
                        }
                    }
                } else {
                    elem_alert.innerHTML = 'An unknown error occurred. Please try again later.';
                    elem_alert.style.display="block";
                }
            fieldset.disabled = false;
            }
        };

        xhr.open('POST', '/api/ui/register');
        xhr.send(data);
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
