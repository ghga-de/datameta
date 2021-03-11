/*
# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

        fetch('/api/v0/forgot',
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
