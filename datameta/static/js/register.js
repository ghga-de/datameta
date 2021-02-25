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
                        var keys = ["name", "email", "org_select", "org_new_name"];
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

        xhr.open('POST', '/register/submit');
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
