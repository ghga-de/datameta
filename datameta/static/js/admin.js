/*
# Copyright 2021 Universität Tübingen
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
    fetch('/api/admin/request',
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
        button.id = "acc_toggle_" + request.id.uuid
        button.innerHTML = request.fullname + " (" + request.email + ")";
        button.setAttribute("data-bs-target", "#acc_collapse_" + request.id.uuid);
        button.setAttribute("aria-controls", "acc_collapse_" + request.id.uuid);

        // The accordion element itself
        var div = clone.querySelector("#acc_collapse");
        div.id = "acc_collapse_" + request.id.uuid;

        // Request id
        clone.querySelector("input.input_id").setAttribute("value", request.id.uuid);

        // Email input
        clone.querySelector("input.input_email").setAttribute("value", request.email);

        // Fullname input
        clone.querySelector("input.input_fullname").setAttribute("value", request.fullname);

        // Fill the group dropdown
        var select = clone.querySelector("select.select_org")
        groups.forEach(function(group) {
            var option = document.createElement("option");
            option.setAttribute("value", group.id.uuid);
            if (group.id.uuid === request.group_id) {
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
    if (!(showreq == '')){
        var admintabs = document.getElementById('admintabs');
        // de-select all tabs
        admintabs.querySelectorAll(".nav-link").forEach(elem => elem.classList.remove("active"))
        admintabs.querySelectorAll(".tab-pane").forEach(elem => elem.classList.remove("show", "active"))
        // account request tab
        admintabs.querySelector("a[data-bs-target='#nav-requests']").classList.add("active");
        admintabs.querySelector("#nav-requests").classList.add("active", "show");
        // open the accordeon
        if(document.getElementById("acc_toggle_"+showreq)) {
            document.getElementById("acc_toggle_"+showreq).classList.remove("collapsed");
            document.getElementById("acc_collapse_"+showreq).classList.add("show");
            document.getElementById("acc_collapse_"+showreq).scrollIntoView({behavior: "smooth", block: "end"});
        } else {
            show_request_alert("The request you are looking for does not exist or was already answered.");
        }

    }
}

/**
 * Reloads the admin view by making an API request and calling the individual
 * update functions for the individual tabs
 */
DataMeta.admin.reload = function() {
    fetch('/api/admin',
        {
            method: 'GET'
        })
        .then(response => response.json())
        .then(function (json) {
            DataMeta.admin.reload_requests(json.reg_requests, json.groups);
            DataMeta.admin.subnav();
            DataMeta.admin.rebuildUserTable(json.users);
            DataMeta.admin.rebuildGroupTable(json.groups);            })
        .catch((error) => {
            console.log(error);
        });

    DataMeta.admin.getAppSettings();
    DataMeta.admin.getMetadata();
}

//Rebuilds the user table, based on the Data fetched from the API
DataMeta.admin.rebuildUserTable = function(users) {
    var t = $('#table_users').DataTable()
    t.clear();
    t.rows.add(users);
    t.draw();   
}

//Initializes the user table
DataMeta.admin.initUserTable = function() {
    $('#table_users').DataTable({
        destroy: true, //Destroys the table, in case it already exist
        rowId: 'id.uuid',
        order: [[1, "asc"]],
        paging : true,
        lengthMenu: [ 25, 50, 75, 100 ],
        pageLength: 25,
        searching: false,
        columns: [
            { title: "User ID", data: "id.site"},
            { title: "Name", data: "fullname", render:function(data) {
                return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="changeUserName(event);" data="' + data + '">' + data + ' <i class="bi bi-pencil-square"></i></button>';
            }},
            { title: "Email Address", data: "email" },
            { title: "Group", data: "group_name", render:function(data) {
                return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="switchGroup(event);" data="' + data + '">' + data + ' <i class="bi bi-pencil-square"></i></button>';
            }},
            { title: "Group ID", data: "group_id.site"},
            { orderable:false, title: "Enabled", data: "enabled", render:function(data) {
                if(data) {
                    return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleUserEnabled(event);"><i class="bi bi-check2"></i></button>'
                } else {
                    return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleUserEnabled(event)";><i class="bi bi-x"></i></button>'
                }
            }},
            { orderable:false, title: "Is Group Admin", data: "group_admin", render:function(data) {
                if(data) {
                    return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleGroupAdmin(event)"><i class="bi bi-check2"></i></button>'
                } else {
                    return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleGroupAdmin(event)"><i class="bi bi-x"></i></button>'
                }
            }},
            { orderable:false, title: "Is Site Admin", data: "site_admin", render:function(data) {
                if(data) {
                    return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleSiteAdmin(event)"><i class="bi bi-check2"></i></button>'
                } else {
                    return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleSiteAdmin(event)"><i class="bi bi-x"></i></button>'
                }
            }}
        ]
    });
}

//Rebuilds the group table, based on the Data fetched from the API
DataMeta.admin.rebuildGroupTable = function(groups) {
    var t = $('#table_groups').DataTable()
    t.clear();
    t.rows.add(groups);
    t.draw();   
}

//Initializes the group table
DataMeta.admin.initGroupTable = function() {
    $('#table_groups').DataTable({
        destroy: true,  //Destroys the table, in case it already exists
        rowId: 'id.uuid',
        order: [[1, "asc"]],
        paging : true,
        lengthMenu: [ 25, 50, 75, 100 ],
        pageLength: 25,
        searching: false,
        columns: [
            { title: "Group ID", data: "id.site"},
            { title: "Group Name", data: "name", render:function(data) {
                return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="changeGroupName(event);" data="' + data + '">' + data + ' <i class="bi bi-pencil-square"></i></button>';
            }},
        ]
    });
}

//Rebuilds the group table, based on the Data fetched from the API
DataMeta.admin.rebuildSiteTable = function(settings) {
    var t = $('#table_site').DataTable()
    t.clear();
    t.rows.add(settings);
    t.draw();   
}

//Initializes the site settings table
DataMeta.admin.initSiteTable = function() {
    $('#table_site').DataTable({
        destroy: true,  //Destroys the table, in case it already exists
        rowId: 'uuid',
        order: [[1, "asc"]],
        paging : true,
        searching: false,
        columns: [
            { title: "Key", data: "key"},
            { title: "Value Type", data: "valueType"},
            { title: "Value", data: "value"},
            { orderable:false, title: "Edit", render:function() {
                return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="enableSettingsEditMode(event);"><i class="bi bi-pencil-square"></i></button>';
            }}
        ]
    });
}

//Rebuilds the group table, based on the Data fetched from the API
DataMeta.admin.rebuildMetadataTable = function(metadata) {
    var t = $('#table_metadata').DataTable()
    t.clear();
    t.rows.add(metadata);
    t.draw();   
}

//Initializes the metadata table
DataMeta.admin.initMetadataTable = function() {
    $('#table_metadata').DataTable({
        destroy: true,  //Destroys the table, in case it already exists
        rowId: 'id.uuid',
        order: [[1, "asc"]],
        paging : true,
        searching: false,
        columns: [
            { title: "Name", data: "name"},
            { title: "Short Description", data: "regexDescription"},
            { title: "Long Description", data: "longDescription"},
            { title: "Regular Expression", data: "regExp"},
            { title: "Date/Time Format", data: "dateTimeFmt"},
            { orderable:false, title: "isMandatory", data: "isMandatory"},
            { title: "Order", data: "order"},
            { orderable:false, title: "isFile", data: "isFile"},
            { orderable:false, title: "isSubmissionUnique", data: "isSubmissionUnique"},
            { orderable:false, title: "isSiteUnique", data: "isSiteUnique"},
            { orderable:false, title: "Edit", render:function() {
                return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="enableMetadataEditMode(event);"><i class="bi bi-pencil-square"></i></button>';
            }}
        ]
    });
}


// Enables the edit mode for Site Settings
function enableSettingsEditMode(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // If the picture in the button was triggered instead of the button itself, change to the button element
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode;

    var innerHTML = row.children[0].innerHTML;
    row.children[0].innerHTML = '<div class="input-group"><input type="text" class="form-control" value="' + innerHTML +'"></div>';

    var innerHTML = row.children[1].innerHTML;
    row.children[1].innerHTML = '<select class="form-select form-select mb-3" aria-label=".form-select-lg example">' +
                                '<option selected>' + innerHTML + '</option>' +
                                '<option value="int">int</option>' +
                                '<option value="string">string</option>' +
                                '<option value="float">float</option>' +
                                '<option value="date">date</option>' +
                                '<option value="time">time</option>' +
                                '</select>'

    innerHTML = row.children[2].innerHTML;
    row.children[2].innerHTML = '<div class="input-group-text"><textarea type="text" class="form-control">' + innerHTML + '</textarea></div>';
    
    row.children[3].innerHTML = '<div style="width:70px"><button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-success enabled" onclick="saveSettings(event);"><i class="bi bi-check2"></i></button>' +
                                '<button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-danger enabled" onclick="DataMeta.admin.getMetadata();"><i class="bi bi-x"></i></button></div>'

    $('#table_site').columns.adjust().draw();
}

// Saves the editing done for Site Settings
function saveSettings(event) {
    // TODO
}

// Enables the edit mode for Metadata Settings
function enableMetadataEditMode(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // If the picture in the button was triggered instead of the button itself, change to the button element
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode;

    var innerHTML = row.children[0].innerHTML;
    row.children[0].innerHTML = '<div class="input-group"><input type="text" class="form-control" value="' + innerHTML +'"></div>';

    innerHTML = row.children[1].innerHTML;
    row.children[1].innerHTML = '<div class="input-group-text"><textarea type="text" class="form-control">' + innerHTML + '</textarea></div>';

    innerHTML = row.children[2].innerHTML;
    row.children[2].innerHTML = '<div class="input-group-text"><textarea type="text" class="form-control">' + innerHTML + '</textarea></div>';

    innerHTML = row.children[3].innerHTML;
    row.children[3].innerHTML = '<div class="input-group"><input type="text" class="form-control" value="' + innerHTML +'"></div>';

    innerHTML = row.children[4].innerHTML;
    row.children[4].innerHTML = '<div class="input-group"><input type="text" class="form-control" value="' + innerHTML +'"></div>';
    
    innerHTML = row.children[5].innerHTML;
    var checked = ((innerHTML == "true") ? "checked": "")
    row.children[5].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" id="flexCheckChecked" '+ checked +'></div'
    
    innerHTML = row.children[6].innerHTML;
    row.children[6].innerHTML = '<div class="input-group"><input type="number" class="form-control" value="' + innerHTML +'"></div>';
    
    innerHTML = row.children[7].innerHTML;
    checked = ((innerHTML == "true") ? "checked": "")
    row.children[7].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" id="flexCheckChecked" '+ checked +'></div'

    innerHTML = row.children[8].innerHTML;
    checked = ((innerHTML == "true") ? "checked": "")
    row.children[8].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" id="flexCheckChecked" '+ checked +'></div'

    innerHTML = row.children[9].innerHTML;
    checked = ((innerHTML == "true") ? "checked": "")
    row.children[9].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" id="flexCheckChecked" '+ checked +'></div'

    row.children[10].innerHTML = '<div style="width:70px"><button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-success enabled" onclick="saveMetadata(event);"><i class="bi bi-check2"></i></button>' +
                                 '<button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-danger enabled" onclick="DataMeta.admin.getMetadata();"><i class="bi bi-x"></i></button></div>'

    $('#table_metadata').columns.adjust().draw();
}

// Saves the editing done for Metadata Settings
function saveMetadata(event) {
    //TODO
}

/**
 * Toggles the group_admin setting for a user
 */
function toggleGroupAdmin(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // If the picture in the button was triggered instead of the button itself, change to the button element
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode;
    var name = row.children[1].children[0].getAttribute('data');
    var group = row.children[3].children[0].getAttribute('data');

    var enabled = button.classList.contains("enabled");

    if(enabled) {
        if(confirm("Do you want to remove the user " + name + " as admin of " + group + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, false, undefined, undefined);
        }
    } else {
        if(confirm("Do you want to make the user " + name + " admin of " + group + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, true, undefined, undefined);
        }
    }
}

/**
 * Toggles the site_admin setting for a user
 */
function toggleSiteAdmin(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // Change the location to the button if the picture was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode;
    var name = row.children[1].children[0].getAttribute('data');

    var enabled = button.classList.contains("enabled");

    if(enabled) {
        if(confirm("Do you want to remove the user " + name + " as site admin?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, false, undefined);
        }
    } else {
        if(confirm("Do you want to make the user " + name + " site admin?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, true, undefined);
        }
    }
}

/**
 * Toggles the enabled setting for a user
 */
function toggleUserEnabled(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // Change the location to the button if the picture was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode;
    var name = row.children[1].children[0].getAttribute('data');

    var enabled = button.classList.contains("enabled");

    if(enabled) {
        if(confirm("Do you want to deactivate the user " + name + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, undefined, false);
        }
    } else {
        if(confirm("Do you want to activate the user " + name + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, undefined, true);
        }
    }
}

/**
 * Switch the Group 
 */
function switchGroup(event) {

    // The button that triggered the function call
    var button = event.srcElement;

      // Change the location to the button if an element inside the button was clicked
      if(button.localName != "button") {
        button = button.parentNode;
    }

    var cell = button.parentNode
    var row = cell.parentNode;
    var uuid = row.id;

    cell.innerHTML =    '<div class="dropdown" style="width:100%">' +
                        '<button class="btn btn-secondary-outline dropdown-toggle" type="button" id="dropdownMenuButton1" data-bs-toggle="dropdown" aria-expanded="false">' +
                        'Choose the new Group:' +
                        '</button>' +
                        '<ul class="dropdown-menu">' +
                        '</ul></div>'

    var dropdownMenu = cell.querySelector(".dropdown-menu");
    var groups = DataMeta.admin.groups;

    for (var i = 0; i < DataMeta.admin.groups.length; i++) {
        var li = document.createElement("li")
        dropdownMenu.appendChild(li);
        var btn = document.createElement("button")
        btn.classList.add("dropdown-item");
        btn.setAttribute("type", "button");
        btn.setAttribute("onClick", " DataMeta.admin.updateUser('"+ uuid +"', undefined, '"+ groups[i].id.uuid +"', undefined, undefined, undefined);")
        btn.innerHTML = groups[i].name;
        li.appendChild(btn);
    }
}

/**
 * Change the name of an user 
 */
function changeUserName(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // Change the location to the button if an element inside the button was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var cell = button.parentNode
    var row = cell.parentNode;
    var name = button.getAttribute('data');
    var uuid = row.id;

    cell.innerHTML =    '<div class="input-group" style="width:200px"><span class="input-group-text">' + 
                        '<i class="bi bi-person-circle"></i>' +
                        '</span>' +
                        '<input name="fullname" type="text" aria-label="Full name" class="input_fullname form-control" value="' + name +'">' +
                        '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onClick="confirmUserNameChange(event, \'' + uuid + '\')"><i class="bi bi-check2"></i></button></div>';
                        
    $('#table_users').columns.adjust().draw();
}

//Confirms the UserNameChange and performs the api call
function confirmUserNameChange(event, uuid) {
    var button = event.srcElement;

    // Change the location to the button if an element inside the button was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var newName = button.parentNode.querySelector("input[name='fullname']").value;

    DataMeta.admin.updateUser(uuid, newName, undefined, undefined, undefined, undefined);
}

/**
 * Change the name of a group 
 */
 function changeGroupName(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // Change the location to the button if an element inside the button was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var cell = button.parentNode
    var row = cell.parentNode;
    var name = button.getAttribute('data');
    var uuid = row.id;

    cell.innerHTML =    '<div class="input-group" style="width:200px"><span class="input-group-text">' + 
                        '<i class="bi bi-person-circle"></i>' +
                        '</span>' +
                        '<input name="fullname" type="text" aria-label="Full name" class="input_fullname form-control" value="' + name +'">' +
                        '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onClick="confirmGroupNameChange(event, \'' + uuid + '\')"><i class="bi bi-check2"></i></button></div>';

    $('#table_groups').columns.adjust().draw();
}

//Confirms the GroupNameChange and performs the api call
function confirmGroupNameChange(event, uuid) {
    var button = event.srcElement;

    // Change the location to the button if an element inside the button was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var newName = button.parentNode.querySelector("input[name='fullname']").value;

    DataMeta.admin.updateGroup(uuid, newName);
}

// API call to change the group name
DataMeta.admin.updateGroup = function (group_id, name) {
    fetch('/api/v0/groups/' + group_id,
    {
        method: 'PUT',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name
        })
    })
    .then(function (response) {
        if(response.status == '204') {
            // Reload Group, User & Request Tables
            DataMeta.admin.reload();
        } else  if (response.status == "400") {
            response.json().then((json) => {
                show_group_alert(json[0].message);
            });
        } else if (response.status == "401") {
            show_group_alert("You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            show_group_alert("You don't have the rights to perform this action.");
        } else {
            show_group_alert("An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// API call to get the AppSettings
DataMeta.admin.getAppSettings = function () {
    fetch('/api/v0/appsettings',
    {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    })
    .then(function (response) {
        if(response.status == '200') {
            response.json().then((json) => {
                // Rebuild Table with the newly fetched Data
                DataMeta.admin.rebuildSiteTable(json);

                // Remove any alerts there still are
                document.getElementById("site_alert").classList.remove("show");
            });
        } else  if (response.status == "400") {
            response.json().then((json) => {
                show_group_alert(json.message);
            });
        } else if (response.status == "401") {
            show_group_alert("You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            show_group_alert("You don't have the rights to perform this action.");
        } else {
            show_group_alert("An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// API call get the Metadata definitions
DataMeta.admin.getMetadata = function () {
    fetch('/api/v0/metadata',
    {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    })
    .then(function (response) {
        if(response.status == '200') {
            response.json().then((json) => {

                // Rebuild Table with the newly fetched Data
                DataMeta.admin.rebuildMetadataTable(json);
                
                // Remove any alerts there still are
                document.getElementById("metadata_alert").classList.remove("show");
            });
        } else  if (response.status == "400") {
            response.json().then((json) => {
                show_group_alert(json.message);
            });
        } else if (response.status == "401") {
            show_group_alert("You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            show_group_alert("You don't have the rights to perform this action.");
        } else {
            show_group_alert("An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}


// Alert in the user Tab for 4** - HTTP Responses
function show_user_alert(text) {
    var al = document.getElementById("user_alert");
    al.classList.remove("show");
    al.innerHTML = text;
    new bootstrap.Collapse(al, { show: true });
}

// Alert in the group Tab for 4** - HTTP Responses
function show_group_alert(text) {
    var al = document.getElementById("group_alert");
    al.classList.remove("show");
    al.innerHTML = text;
    new bootstrap.Collapse(al, { show: true });
}

// Alert in the request Tab
function show_request_alert(text) {
    var al = document.getElementById("request_alert");
    al.classList.remove("show");
    al.innerHTML = text;
    new bootstrap.Collapse(al, { show: true });
}

// API call to change user name, group, admin and enabled settings
DataMeta.admin.updateUser = function (id, name, groupId, groupAdmin, siteAdmin, enabled) {
    fetch('/api/v0/users/' + id,
    {
        method: 'PUT',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
            groupId,
            groupAdmin,
            siteAdmin,
            enabled
        })
    })
    .then(function (response) {
        if(response.status == '204') {
            // Reload Group, User & Request Tables
            DataMeta.admin.reload();
        } else if (response.status == "400") {
            response.json().then((json) => {
                show_user_alert(json[0].message);
            });
        } else if (response.status == "401") {
            show_user_alert("You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            show_user_alert("You don't have the rights to perform this action.");
        } else if (response.status == "404") {
            show_user_alert("The user or group you are referring to does not exist.");
        } else {
            show_user_alert("An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

function clearAlerts () {
    document.getElementById("group_alert").classList.remove("show");
    document.getElementById("user_alert").classList.remove("show");
    document.getElementById("request_alert").classList.remove("show");
    document.getElementById("site_alert").classList.remove("show");
    document.getElementById("metadata_alert").classList.remove("show");
}

window.addEventListener("load", function() {
    DataMeta.admin.initSiteTable();
    DataMeta.admin.initMetadataTable();
    DataMeta.admin.initUserTable();
    DataMeta.admin.initGroupTable();
    DataMeta.admin.reload();
    document.getElementById("nav-site-tab").addEventListener("click", clearAlerts);
    document.getElementById("nav-metadata-tab").addEventListener("click", clearAlerts);
    document.getElementById("nav-groups-tab").addEventListener("click", clearAlerts);
    document.getElementById("nav-users-tab").addEventListener("click", clearAlerts);
    document.getElementById("nav-requests-tab").addEventListener("click", clearAlerts);
});
