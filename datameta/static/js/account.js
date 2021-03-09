/*
# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#          Moritz Hahn <moritz.hahn@uni-tuebingen.de>
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
*/

window.addEventListener("load", function() {

    function view_success() {
        new bootstrap.Collapse(document.getElementById("success"), { show: true })
        clear_form();
    }

    function show_alert(text) {
        var al = document.getElementById("alert");
        al.innerHTML = text;
        new bootstrap.Collapse(al, { show: true });
    }

    function clear_form() {
        document.getElementById("new_password").classList.remove("is-invalid")
        document.getElementById("new_password_repeat").classList.remove("is-invalid")
        document.getElementById("change_password_form").reset();
    }

    function clear_alerts() {
        document.getElementById("alert").classList.remove("show");
        document.getElementById("success").classList.remove("show");
    }

    document.getElementById("change_password_tab").addEventListener("click", function() {
        clear_form();
        clear_alerts();
    });

    document.getElementById("change_password_form").addEventListener("submit", function(event) {  

        // Prevent form submission
        event.preventDefault();

        clear_alerts();

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
        fetch('/api/users/' + data.get("uuid") + '/password',
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
                if (response.status == "204") {
                    view_success();
                    return;
                } else {
                    if (response.status == "401") {
                        show_alert("You have to be logged in to perform this action.");
                    } else if (response.status == "403") {
                        show_alert("Wrong password.");
                    } else if(response.status == "400") {
                        show_alert("Your password has to have at least 10 Characters");   
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
        clear_api_alerts();        
        var al = document.getElementById("api_alert");
        al.innerHTML = text;
        new bootstrap.Collapse(al, { show: true });
    }

    function show_api_success(text) {
        clear_api_alerts();        
        var success = document.getElementById("api_success");
        success.innerHTML = text;
        new bootstrap.Collapse(success, { show: true });
    }

    function clear_api_form() {
        document.getElementById("label").classList.remove("is-invalid");
        document.getElementById("expires").classList.remove("is-invalid");
        document.getElementById("add_api_key_form").reset();
    }

    // Adds an Api Key to the table
    function add_api_key(apiKey) {
        var id = apiKey.apiKeyId;
        var label = apiKey.label;
        var tableBody = document.getElementById("tbody_apikeys");

        var row = tableBody.insertRow();
        row.id = apiKey.apiKeyId;

        var cell1 = row.insertCell();
        var cell2 = row.insertCell();
        var cell3 = row.insertCell();
        
        cell1.innerHTML = label;
        cell2.innerHTML = apiKey.expiresAt;
        cell3.innerHTML = '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger"><i class="bi bi-trash-fill"></i></button>'
        cell3.querySelector(".btn").addEventListener("click", function(event) {
            delete_api_key(label, id);
        });
    }

    // Deletes an API key from the table and database
    function delete_api_key(label, id) {
        
        // API call
        fetch('/api/keys/' + id ,
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
            } else if (response.status == "400" || response.status == "500") {
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
    function clear_api_alerts() {
        document.getElementById("api_alert").classList.remove("show");
        document.getElementById("api_success").classList.remove("show");
    }

    uuid = document.getElementById("uuid").value;

    //Gets all the API keys and adds them to the table
    fetch('/api/users/' + uuid + '/keys',
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
        } else if (response.status == "400" || response.status == "500") {
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
        clear_api_alerts();
        clear_api_form();
    }); 

    // Sets the min and max date strings for the date input.
    function set_date(date) {

        var dd = date.getDate();
        var mm = date.getMonth() + 1; //January is 0!
        var yyyy = date.getFullYear();
    
        if (dd < 10) {
        dd = '0' + dd
        }
    
        if (mm < 10) {
        mm = '0' + mm
        }
        date = yyyy + '-' + mm + '-' + dd;

        return date
    }

    // Needs to be adjusted once it is a property in the config file. Using 1 year for testing
    var days = 365;

    var min = new Date();
    var max = new Date(min);
    max.setDate(min.getDate() + days);
    document.getElementById('expires').setAttribute("min", set_date(min));
    document.getElementById('expires').setAttribute("max", set_date(max));

    document.getElementById("add_api_key_form").addEventListener("submit", function(event) {  

        event.preventDefault();

        var form = event.target;

        // Validataion
        var data = new FormData(form);
        var label = data.get("label");
        var expires = new Date(data.get("expires"));
        expires = expires.toISOString();

        if (label == "") {
            document.getElementById("label").classList.add("is-invalid");
            return;
        }else if (expires == "") {
            document.getElementById("label").classList.remove("is-invalid");
            document.getElementById("expires").classList.add("is-invalid");
            return;
        } else {
            document.getElementById("label").classList.remove("is-invalid");
            document.getElementById("expires").classList.remove("is-invalid");
        } 

        // POST API key
        fetch('/api/keys',
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
            } else  if (response.status == "400" || response.status == "500") {
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
        }).catch((error) => {
            console.log(error);
            show_api_alert("An unknown error occurred. Please try again later.");
        });
    });
});
