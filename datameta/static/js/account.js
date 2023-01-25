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

DataMeta.account = {};

window.addEventListener("dmready", function() {

    function view_success() {
        new bootstrap.Collapse(document.getElementById("success"), { show: true })
        clear_form();
    }

    function show_alert(text) {
        var al = document.getElementById("alert");
        al.innerHTML = text +  '\n <button type="button" class="btn-close" id="dismiss_alert" onclick="DataMeta.account.clear_alerts()"></button>';
        new bootstrap.Collapse(al, { show: true });
    }

    function clear_form() {
        document.getElementById("new_password").classList.remove("is-invalid")
        document.getElementById("new_password_repeat").classList.remove("is-invalid")
        document.getElementById("change_password_form").reset();
    }

    DataMeta.account.clear_alerts = function() {
        document.getElementById("alert").classList.remove("show");
        document.getElementById("success").classList.remove("show");
    }

    document.getElementById("change_password_tab").addEventListener("click", function() {
        clear_form();
        DataMeta.account.clear_alerts();
    });

    document.getElementById("change_password_form").addEventListener("submit", function(event) {  

        // Prevent form submission
        event.preventDefault();

        DataMeta.account.clear_alerts();

        var form = event.target;

        // Validataion
        var data = new FormData(form);

        if (data.get("new_password") != data.get("new_password_repeat")) {
            document.getElementById("new_password").classList.add("is-invalid")
            document.getElementById("new_password_repeat").classList.add("is-invalid")
            return;
        } else {
            document.getElementById("new_password").classList.remove("is-invalid")
            document.getElementById("new_password_repeat").classList.remove("is-invalid")
        }
        // Talk to the API
        fetch(DataMeta.api('users/' + DataMeta.user.id.uuid + '/password'),
            {
                method: 'put',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    passwordChangeCredential: data.get("old_password"),
                    newPassword: data.get("new_password")
                })
            })
            .then((response) => {
                if (response.status == "200") {
                    view_success();
                    return;
                } else {
                    if (response.status == "401") {
                        show_alert("You have to be logged in to perform this action.");
                    } else if (response.status == "403") {
                        show_alert("Wrong password.");
                    } else if(response.status == "400") {
                        response.json().then((json) => {
                            show_alert(json[0].message);
                        });
                    } else {
                        show_alert("An unknown error occurred. Please try again later.");
                    }
                }
            })
            .catch((error) => {
                console.log(error);
                show_alert("An unknown error occurred. Please try again later.");
            });
    });

    function show_api_alert(text) {
        DataMeta.account.clear_api_alerts();        
        var al = document.getElementById("api_alert");
        al.innerHTML = text + '\n <button type="button" class="btn-close" onclick="DataMeta.account.clear_api_alerts()" id="dismiss_api_alert"></button>';
        new bootstrap.Collapse(al, { show: true });
    }

    function show_api_success(text) {
        DataMeta.account.clear_api_alerts();        
        var success = document.getElementById("api_success");
        success.innerHTML = text + '\n <button type="button" class="btn-close" onclick="DataMeta.account.clear_api_alerts()" id="dismiss_api_success"></button>';
        new bootstrap.Collapse(success, { show: true });
    }

    function clear_api_form() {
        document.getElementById("label").classList.remove("is-invalid");
        document.getElementById("expires").classList.remove("is-invalid");
        document.getElementById("add_api_key_form").reset();
    }

    // Adds an Api Key to the table
    function add_api_key(apikey) {
        var id = apikey.id.uuid;
        var label = apikey.label;
        var tableBody = document.getElementById("tbody_apikeys");

        var row = tableBody.insertRow();
        row.id = id;

        var cell1 = row.insertCell();
        var cell2 = row.insertCell();
        var cell3 = row.insertCell();
        
        cell1.innerHTML = label;
        cell2.innerHTML = apikey.expires.split('T')[0];
        cell3.innerHTML = '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger"><i class="bi bi-trash-fill"></i></button>'
        cell3.querySelector(".btn").addEventListener("click", function(event) {
            delete_api_key(label, id);
        });
    }

    // Deletes an API key from the table and database
    function delete_api_key(label, id) {
        
        // API call
        fetch(DataMeta.api('keys/' + id),
        {
            method: 'delete',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
        })
        .then((response) => {
            if (response.status == "200") {
                // Only deletes key in table, if deletion in database was successfull
                var row = document.getElementById(id);
                document.getElementById("tbody_apikeys").removeChild(row); 
                show_api_success("Key '" + label + "' has been removed successfully.");
            } else if (response.status == "400") {
                response.json().then((json) => {
                    show_api_alert(json.message);
                });
            } else if (response.status == "401") {
                show_api_alert("You have to be logged in to perform this action.");
            } else {
                show_api_alert("An unknown error occurred. Please try again later.");
            }
        })
        .catch((error) => {
            console.log(error);
            show_api_alert("An unknown error occurred. Please try again later.");
        });
    }

    // Clears the success and alert boxes
    DataMeta.account.clear_api_alerts = function() {
        document.getElementById("api_alert").classList.remove("show");
        document.getElementById("api_success").classList.remove("show");
    }

    //Gets all the API keys and adds them to the table
    fetch(DataMeta.api('users/' + DataMeta.user.id.uuid + '/keys'),
    {
        method: 'get',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    })
    .then((response) => {
        if (response.status == "200") {
            response.json().then((json) => {
                json.forEach(function (apikey, index) {
                    add_api_key(apikey);
            });
        });
        } else if (response.status == "400") {
            response.json().then((json) => {
                show_api_alert(json.message);
            });
        } else if (response.status == "401") {
            show_api_alert("You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            show_api_alert("You don't have the rights to perform this action.");
        } else {
            show_api_alert("An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
        show_api_alert("An unknown error occurred. Please try again later.");
    });

    document.getElementById("api_keys_tab").addEventListener("click", function() {
        DataMeta.account.clear_api_alerts();
        clear_api_form();
    }); 

    // Sets the min Date String for the date field as today
    var min = new Date();  
    document.getElementById('expires').setAttribute("min", min.toISOString().split('T')[0]);

    document.getElementById("add_api_key_form").addEventListener("submit", function(event) {  

        event.preventDefault();

        var form = event.target;

        // Validataion
        var data = new FormData(form);
        var label = data.get("label");
        var expires = new Date(data.get("expires"));

        try {
            expires = expires.toISOString().split('T')[0];
        } catch (error) {
            document.getElementById("expires").classList.add("is-invalid");
            return;
        }

        if (label == "") {
            document.getElementById("expires").classList.remove("is-invalid");
            document.getElementById("label").classList.add("is-invalid");
            return;
        } else {
            document.getElementById("label").classList.remove("is-invalid");
            document.getElementById("expires").classList.remove("is-invalid");
        } 

        // POST API key
        fetch(DataMeta.api('keys'),
            {
                method: 'post',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    label : label,
                    expires : expires
                })
        }).then((response) => {
            if (response.status == "200") {
                response.json().then((json) => {
                    add_api_key(json);
                    show_api_success("Your new API key '" + label +"' is:<br>" + json.token);
                });
            } else  if (response.status == "400") {
                response.json().then((json) => {
                    show_api_alert(json[0].message);
                });
            } else if (response.status == "401") {
                show_api_alert("You have to be logged in to perform this action.");
            } else if (response.status == "403") {
                show_api_alert("You don't have the rights to perform this action.");
            } else {
                show_api_alert("An unknown error occurred. Please try again later.");
            }
        }).catch((error) => {
            console.log(error);
            show_api_alert("An unknown error occurred. Please try again later.");
        });
    });
});
