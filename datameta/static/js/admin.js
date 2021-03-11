/*
# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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

"use strict"; 

DataMeta.admin = {}

/**
 * Make an API request for answering to a user registration request
 */
DataMeta.admin.answer_request = function(accept, form) {
    var fdata = new FormData(form);
    var response = accept ? "accept" : "reject";
    var json_body = JSON.stringify({
        id: fdata.get("id"),
        response: response,
        group_admin: (fdata.get("group_admin") == "on"),
        group_newname: fdata.get("group_newname"),
        group_id: fdata.get("group_id") == -1 ? null :fdata.get("group_id"),
        fullname: fdata.get("fullname")
    });
    fetch('/api/v0/admin/request',
        {
            method: 'put',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: json_body
        })
        .then(function(response) {
            if (response.status == 204) {
                DataMeta.admin.reload();
            } else {
                alert("An unknown error occurred");
                console.log(response);
                DataMeta.admin.reload();
            }
        })
        .catch((error) => {
            console.log(error);
            DataMeta.admin.reload();
        });
}

/**
 * Reloads the requests tab on the admin page, given a json response from the API
 */
DataMeta.admin.reload_requests = function(requests, groups) {
    var accordion = document.getElementById("requests");
    // Remove all items
    accordion.querySelectorAll(".accordion-item").forEach(e => e.remove());

    // Re-generate them
    if (requests.length==0) {
        document.getElementById("req_title").innerHTML = "No pending Account Requests";
    } else {
        document.getElementById("req_title").innerHTML = "Pending Account Requests";
    }
    requests.forEach(function(request) {
        var template = document.getElementById("template_request");
        var clone = template.content.firstElementChild.cloneNode(true);
        var button = clone.querySelector("#acc_toggle");

        // Button unfolding the accordion element
        button.id = "acc_toggle_" + request.id
        button.innerHTML = request.fullname + " (" + request.email + ")";
        button.setAttribute("data-bs-target", "#acc_collapse_" + request.id);
        button.setAttribute("aria-controls", "acc_collapse_" + request.id);

        // The accordion element itself
        var div = clone.querySelector("#acc_collapse");
        div.id = "acc_collapse_" + request.id;

        // Request id
        clone.querySelector("input.input_id").setAttribute("value", request.id);

        // Email input
        clone.querySelector("input.input_email").setAttribute("value", request.email);

        // Fullname input
        clone.querySelector("input.input_fullname").setAttribute("value", request.fullname);

        // Fill the group dropdown
        var select = clone.querySelector("select.select_org")
        groups.forEach(function(group) {
            var option = document.createElement("option");
            option.setAttribute("value", group.id);
            if (group.id === request.group_id) {
                option.selected=true;
            }
            option.innerHTML = group.name;
            select.appendChild(option);
        });

        // Pre-select radio and fill new group name
        var radio_new_org = clone.querySelector("input.radio_new_org");
        var radio_existing_org = clone.querySelector("input.radio_existing_org");
        if (request.group_id===null) {
            radio_new_org.checked = true;
            clone.querySelector("input.input_new_org").setAttribute("value", request.new_group_name);
        } else {
            radio_existing_org.checked = true;
        }

        var form = clone.querySelector("form");
        var btn_reject = clone.querySelector("button.req_reject");
        var btn_accept = clone.querySelector("button.req_accept");
        btn_reject.addEventListener("click", function(e) {
            btn_reject.disabled = true;
            btn_accept.disabled = true;
            DataMeta.admin.answer_request(false, form);
        });
        btn_accept.addEventListener("click", function(e) {
            btn_reject.disabled = true;
            btn_accept.disabled = true;
            DataMeta.admin.answer_request(true, form);
        });

        // Automatic radio switch for org
        clone.querySelector("input.input_new_org").addEventListener("keydown", function(e) {
            radio_new_org.checked = true;
            radio_existing_org.checked = false;
        });
        clone.querySelector("select.select_org").addEventListener("change", function(e) {
            radio_new_org.checked = false;
            radio_existing_org.checked = true;
        });

        accordion.append(clone);
    });
}


DataMeta.admin.subnav = function() {
    // Handle registration request preselection
    var showreq = DataMeta.uilocal.showreq;
    DataMeta.uilocal.showreq = null;
    if (showreq != null) {
        var admintabs = document.getElementById('admintabs');
        // de-select all tabs
        admintabs.querySelectorAll(".nav-link").forEach(elem => elem.classList.remove("active"))
        admintabs.querySelectorAll(".tab-pane").forEach(elem => elem.classList.remove("show", "active"))
        // account request tab
        admintabs.querySelector("a[data-bs-target='#nav-requests']").classList.add("active");
        admintabs.querySelector("#nav-requests").classList.add("active", "show");
        // open the accordeon
        document.getElementById("acc_toggle_"+showreq).classList.remove("collapsed");
        document.getElementById("acc_collapse_"+showreq).classList.add("show");
        document.getElementById("acc_collapse_"+showreq).scrollIntoView({behavior: "smooth", block: "end"});
    }
}

/**
 * Reloads the admin view by making an API request and calling the individual
 * update functions for the individual tabs
 */
DataMeta.admin.reload = function() {
        fetch('/api/v0/admin',
            {
                method: 'GET'
            })
            .then(response => response.json())
            .then(function (json) {
                DataMeta.admin.reload_requests(json.reg_requests, json.groups);
                DataMeta.admin.subnav();
            })
            .catch((error) => {
                console.log(error);
            });
}

window.addEventListener("load", function() {
    DataMeta.admin.reload();
});
