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
        var al = document.getElementById("api_alert");
        al.innerHTML = text;
        new bootstrap.Collapse(al, { show: true });
    }

    function show_api_success(text) {
        var al = document.getElementById("api_success");
        al.innerHTML = text;
        new bootstrap.Collapse(al, { show: true });
    }

    function clear_api_form() {
        document.getElementById("label").classList.remove("is-invalid")
        document.getElementById("add_api_key_form").reset();
    }

    // Adds an Api Key to the table
    function add_api_key(apikey) {
        table = document.getElementById("table_apikeys");
        row = table.insertRow();
        row.id = label
        cell1 = row.insertCell();
        cell2 = row.insertCell();
        cell3 = row.insertCell();
        cell1.innerHTML = apikey.label;
        cell2.innerHTML = apikey.expiresAt;
        cell3.innerHTML = '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger"><i class="bi bi-trash-fill"></i></button>'
        cell3.querySelector(".btn").addEventListener("click", function(event) {
            delete_api_key(label);
        });
    }

    // Deletes an API key from the table and database
    function delete_api_key(label) {
        //TODO DELTE key

        //TODO: Only do this, if deletion was successfull
        row = document.getElementById(label);
        document.getElementById("tbody_apikeys").removeChild(row); 
        show_api_success("Key " + label + " has been removed successfully.");
    }

    // Clears the success and alert boxes
    function clear_api_alerts() {
        api_alert = document.getElementById("api_alert");
        api_success = document.getElementById("api_success");
        api_alert.innerHTML = "";
        api_success.innerHTML = "";
        api_alert.classList.remove("show");
        api_success.classList.remove("show");
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
        } else {
            if (response.status == "400" || response.status == "500") {
                response.json().then((json) => {
                    show_api_alert(json.message);
                });
            } else if (response.status == "401") {
                show_api_alert("You have to be logged in to perform this action.");
            } else {
                show_api_alert("An unknown error occurred. Please try again later.");
            }
        }
    })
    .catch((error) => {
        console.log(error);
        show_alert("An unknown error occurred. Please try again later.");
    });

    document.getElementById("api_keys_tab").addEventListener("click", function() {
        clear_api_alerts();
        clear_api_form();
    }); 

    document.getElementById("generate_api_key_button").addEventListener("click", function() {

        // TODO: Open Form: Label && Expiration Date, get both from form
        //

        label = "test";

        d = new Date();
        d.setTime(d.getTime() + 24*60*60*1000);
        expires = d.toUTCString();

        // POST API key
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
                document.resp = response;
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

        // Post Return Value to table && success box

    });

     

});
