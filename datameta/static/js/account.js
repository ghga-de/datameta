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
    });
});
