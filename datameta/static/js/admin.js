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
        group_id: fdata.get("group_id") == -1 || fdata.get("new_org") == 0 ? null :fdata.get("group_id"),
        fullname: fdata.get("fullname")
    });
    fetch('/api/ui/admin/request',
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
    if (!(showreq == '' || showreq == null)){
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
            showAlert("requests_alert", "The request you are looking for does not exist or was already answered.");
        }

    }
}

/**
 * Reloads the admin view by making an API request and calling the individual
 * update functions for the individual tabs
 */
DataMeta.admin.reload = function() {
    fetch('/api/ui/admin',
        {
            method: 'GET'
        })
        .then(response => response.json())
        .then(function (json) {

            DataMeta.admin.reload_requests(json.reg_requests, json.groups);
            DataMeta.admin.subnav();
            DataMeta.admin.rebuildUsersTable(json.users);
            DataMeta.admin.groups = json.groups;
            DataMeta.admin.users = json.users;

            if (DataMeta.user.siteAdmin) {
                document.getElementById("nav-groups-tab-li").style.display = "block";
                document.getElementById("nav-metadata-tab-li").style.display = "block";
                document.getElementById("nav-site-tab-li").style.display = "block";
                document.getElementById("nav-services-tab-li").style.display = "block";
                DataMeta.admin.getAppSettings();
                DataMeta.admin.getServices();
                DataMeta.admin.getMetadata();
                DataMeta.admin.rebuildGroupsTable(json.groups);
            }
        })
        .catch((error) => {
            console.log(error);
        });

}

//Rebuilds the user table, based on the Data fetched from the API
DataMeta.admin.rebuildUsersTable = function(users) {
    var t = $('#table_users').DataTable();
    t.clear();
    t.rows.add(users);
    t.columns.adjust().draw();
}

//Initializes the user table
DataMeta.admin.initUsersTable = function() {
    $('#table_users').DataTable({
        rowId: 'id.uuid',
        order: [[1, "asc"]],
        paging : true,
        lengthMenu: [ 10, 25, 50, 100 ],
        pageLength: 25,
        searching: true,
        scrollX: true,
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
            { title: "Enabled", data: "enabled", render:function(data, type, row) {
                if ( type === 'display' || type === 'filter' ) {
                    if(data) {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleUserEnabled(event);"><i class="bi bi-check2"></i></button>'
                    } else {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleUserEnabled(event)";><i class="bi bi-x"></i></button>'
                    }
                }
                return Boolean(data);
            }},
            { title: "Site Read", data: "site_read", render:function(data, type, row) {
                if ( type === 'display' || type === 'filter' ) {
                    if(data) {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleSiteRead(event);"><i class="bi bi-check2"></i></button>'
                    } else {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleSiteRead(event)";><i class="bi bi-x"></i></button>'
                    }
                }
                return Boolean(data);
            }},
            { title: "Is Group Admin", data: "group_admin", render:function(data, type, row) {
                if ( type === 'display' || type === 'filter' ) {
                    if(data) {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleGroupAdmin(event)"><i class="bi bi-check2"></i></button>'
                    } else {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleGroupAdmin(event)"><i class="bi bi-x"></i></button>'
                    }
                }
                return Boolean(data);
            }},
            { title: "Is Site Admin", data: "site_admin", render:function(data, type, row) {
                if ( type === 'display' || type === 'filter' ) {
                    if(data) {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onclick="toggleSiteAdmin(event)"><i class="bi bi-check2"></i></button>'
                    } else {
                        return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" onclick="toggleSiteAdmin(event)"><i class="bi bi-x"></i></button>'
                    }
                }
                return Boolean(data);
            }}
        ]
    });
}

//Rebuilds the group table, based on the Data fetched from the API
DataMeta.admin.rebuildGroupsTable = function(groups) {
    var t = $('#table_groups').DataTable();
    t.clear();
    t.rows.add(groups);
    t.draw();
}

//Initializes the group table
DataMeta.admin.initGroupsTable = function() {
    $('#table_groups').DataTable({
        rowId: 'id.uuid',
        order: [[1, "asc"]],
        paging : true,
        lengthMenu: [ 10, 25, 50, 100 ],
        pageLength: 25,
        searching: false,
        scrollX: true,
        columns: [
            { title: "Group ID", data: "id.site"},
            { title: "Group Name", data: "name", render:function(data) {
                return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="changeGroupName(event);" data="' + data + '">' + data + ' <i class="bi bi-pencil-square"></i></button>';
            }},
        ]
    });
}

//Rebuilds the site settings table, based on the Data fetched from the API
DataMeta.admin.rebuildSiteTable = function(settings) {
    var t = $('#table_site').DataTable()
    t.clear();
    t.rows.add(settings);
    t.draw();
}

//Initializes the site settings table
DataMeta.admin.initSiteTable = function() {
    if($('#table_site')) {
        $('#table_site').DataTable({
            rowId: 'id.uuid',
            order: [[1, "asc"]],
            paging : true,
            pageLength: 25,
            searching: false,
            scrollX: true,
            columns: [
                { title: "Key", data: "key"},
                { title: "Value Type", data: "valueType"},
                { title: "Value", data: "value", render:function(data) {
                    return  '<div id="settings_data">' + $.fn.DataTable.render.text().display(data) +
                            '</div><button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="enableSettingsEditMode(event);"><i class="bi bi-pencil-square"></i></button>';
                }},
            ]
        });
    }
}

//Rebuilds the services table, based on the Data fetched from the API
DataMeta.admin.rebuildServicesTable = function(services) {
    var t = $('#table_services').DataTable()
    t.clear();
    t.rows.add(services);
    t.draw();
}

//Initializes the services table
DataMeta.admin.initServicesTable = function() {
    if($('#table_services')) {
        $('#table_services').DataTable({
            rowId: 'id.uuid',
            order: [[1, "asc"]],
            paging : true,
            pageLength: 25,
            searching: false,
            scrollX: true,
            columns: [
                { title: "Service ID", data: "id.site"},
                { title: "Service Name", data: "name", render:function(data) {
                    return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="changeServiceName(event);" data="' + data + '">' + data + ' <i class="bi bi-pencil-square"></i></button>';
                }},
                { title: "Users", data: {}, render: function(data) {
                    // ToDo: Add Drop-Down Menu for all users
                    var uuid = data.id.uuid;
                    var length = data.userIds.length;

                    var userString;
                    if(length == 1) {
                        userString = "1 User"
                    } else {
                        userString = length + " Users"
                    }

                    /**
                     * Add an accordion, which includes a list of all users,
                     * and the possibility to change this user list
                     */
                    var returnString =  '<div class="accordion" id="accordion-' + uuid + '">' +
                        '<div class="accordion-item">' +
                        '<h2 class="accordion-header" id="heading-' + uuid + '">' +
                        '<button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-' + uuid + '" aria-expanded="false" aria-controls="collapse-' + uuid + '">' +
                        userString + '</button></h2>' +
                        '<div id="collapse-' + uuid + '" class="accordion-collapse collapse" aria-labelledby="heading-' + uuid + '" data-bs-parent="#accordion-' + uuid + '">' +
                        '<div class="accordion-body">' +
                        '<ul class="list-group mb-3">'

                    data.userIds.forEach((userId) => {

                        var userName = "";

                        DataMeta.admin.users.forEach((user) => {
                            if(userId.uuid == user.id.uuid) {
                                userName = user.fullname;
                            } 
                        })

                        returnString = returnString + '<li class="list-group-item" data-datameta-userid="' + userId.uuid + '">' + userName + '</li>'
                    })

                    returnString = returnString + '</ul>' +
                        '<button class="btn btn-sm btn-warning enabled w-100 mb-3" type="button" onclick="DataMeta.admin.editServiceUsers(event, \'' + uuid + '\')">Edit Users</button>' +
                        '<input id="user-id-input-' + uuid + '" type="text" name="user_id" placeholder=" Enter User ID" class="w-100 mb-2">' +                     
                        '<button class="btn btn-outline-success enabled w-100" type="button" onclick="DataMeta.admin.addServiceUser(\'' + uuid + '\')">Add User to Service</button>' +
                        '</div></div></div></div>';
                    
                    return returnString;
                }}
            ]
        });
    }
}

//Rebuilds the metadata table, based on the Data fetched from the API
DataMeta.admin.rebuildMetadataTable = function(metadata) {
    var t = $('#table_metadata').DataTable()
    t.clear();
    t.rows.add(metadata);
    t.draw();
}

//Initializes the metadata table
DataMeta.admin.initMetadataTable = function() {
    if($('#table_metadata')) {
        $('#table_metadata').DataTable({
            rowId: 'id.uuid',
            order: [[7, "asc"]],
            paging : true,
            pageLength: 25,
            searching: false,
            scrollX: true,
            columns: [
                { title: "Name", data: "name"},
                { title: "Short Description", data: "regexDescription"},
                { title: "Long Description", data: "longDescription"},
                { title: "Example", data: "example"},
                { title: "Regular Expression", data: "regExp"},
                { title: "Date/Time Format", data: "dateTimeFmt"},
                { orderable:false, title: "isMandatory", data: "isMandatory"},
                { title: "Order", data: "order"},
                { orderable:false, title: "isFile", data: "isFile"},
                { orderable:false, title: "isSubmissionUnique", data: "isSubmissionUnique"},
                { orderable:false, title: "isSiteUnique", data: "isSiteUnique"},
                { orderable:false, title: "Service", data: "serviceId", render:function(data) {
                    if(data) {
                        var name;
                        DataMeta.admin.services.forEach((service) => {
                            if(service.id.uuid == data.uuid) {
                                name = service.name
                            }
                        });
                        return name
                    } else {
                        return '<span class="text-black-50"><i>empty</i></span>' 
                    }
                }},
                { orderable:false, title: "Edit", render:function() {
                    return '<button type="button" class="py-0 px-1 btn btn-sm enabled" onclick="enableMetaDatumEditMode(event);"><i class="bi bi-pencil-square"></i></button>';
                }}
            ]
        });
    }
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

    var data = button.parentNode.querySelector("#settings_data").innerHTML;

    row.children[2].innerHTML = '<div class="input-group" style="width:100%"><span class="input-group-text">' +
                                '<i class="bi bi-pencil"></i>' +
                                '</span>' +
                                '<textarea type="text" class="form-control">' + data + '</textarea>' +
                                '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onClick="saveSettings(event);"><i class="bi bi-check2"></i></button></div>';

    $('#table_site').DataTable().columns.adjust().draw();
}

// Saves the editing done for Site Settings
function saveSettings(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // If the picture in the button was triggered instead of the button itself, change to the button element
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode.parentNode;

    var appsetting_id = row.id;
    var value = row.children[2].querySelector('textarea').value;

    fetch(DataMeta.api('appsettings/' + appsetting_id),
    {
        method: 'PUT',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            value
        })
    })
    .then(function (response) {
        if(response.status == '204') {
            // Reload Metadata Table
            DataMeta.admin.getAppSettings();

            // Remove any alerts there still are
            document.getElementById("site_alert").classList.remove("show");
        } else  if (response.status == "400") {
            response.json().then((json) => {
                showAlert("site_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("site_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("site_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("site_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// Enables the edit mode for Metadata Settings
function enableMetaDatumEditMode(event) {

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
    row.children[5].innerHTML = '<div class="input-group"><input type="text" class="form-control" value="' + innerHTML +'"></div>';

    innerHTML = row.children[6].innerHTML;
    var checked = ((innerHTML == "true") ? "checked": "")
    row.children[6].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" '+ checked +'></div>';

    innerHTML = row.children[7].innerHTML;
    row.children[7].innerHTML = '<div class="input-group" style="width:70px"><input type="number" class="form-control" value="' + innerHTML +'"></div>';

    innerHTML = row.children[8].innerHTML;
    checked = ((innerHTML == "true") ? "checked": "")
    row.children[8].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" '+ checked +'></div>';

    innerHTML = row.children[9].innerHTML;
    checked = ((innerHTML == "true") ? "checked": "")
    row.children[9].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" '+ checked +'></div>';

    innerHTML = row.children[10].innerHTML;
    checked = ((innerHTML == "true") ? "checked": "")
    row.children[10].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value="" '+ checked +'></div>';

    row.children[11].innerHTML =    
        '<select class="form-select">' +
            '<option selected value="">No Service</option>' +
        '</select>'

    var serviceSelect = row.children[11].querySelector(".form-select");
    var services = DataMeta.admin.services;

    for (var i = 0; i < DataMeta.admin.services.length; i++) {
        var option = document.createElement("option")
        option.setAttribute('value', services[i].id.uuid);
        serviceSelect.appendChild(option);
        option.innerHTML = services[i].name;
    }

    row.children[12].innerHTML = '<div style="width:70px"><button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-success enabled" onclick="saveMetaDatum(event);"><i class="bi bi-check2"></i></button>' +
                                 '<button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-danger enabled" onclick="DataMeta.admin.getMetadata();"><i class="bi bi-x"></i></button></div>'

    $('#table_metadata').DataTable().columns.adjust().draw();
}

// Enables the edit mode for a new Metadatum
DataMeta.admin.newMetaDatumRow = function() {

    var table = $('#table_metadata').DataTable();
    var rows = table.rows();

    // Check, if there is already a new row
    for (row in rows) {
        if (row.id == "-1") {
            showAlert("metadata_alert", "You can only create one new metadatum at a time.")
            return;
        }
    }

    // create a new row
    var row = [{
        id: {uuid: "-1"},
        name: "",
        regexDescription: "",
        longDescription: "",
        example: "",
        regExp: "",
        dateTimeFmt: "",
        isMandatory: "",
        order: "0",
        isFile: "",
        isSubmissionUnique: "",
        isSiteUnique: "",
        serviceId: ""}];

    // add the new row to the table
    table.rows.add(row);
    table.order([7, "desc"]).columns.adjust().draw();

    var row = document.getElementById("-1");

    //Immediately make the row editable
    row.children[0].innerHTML = '<div class="input-group"><input type="text" class="form-control" value=""></div>';
    row.children[1].innerHTML = '<div class="input-group-text"><textarea type="text" class="form-control"></textarea></div>';
    row.children[2].innerHTML = '<div class="input-group-text"><textarea type="text" class="form-control"></textarea></div>';
    row.children[3].innerHTML = '<div class="input-group"><input type="text" class="form-control" value=""></div>';
    row.children[4].innerHTML = '<div class="input-group"><input type="text" class="form-control" value=""></div>';
    row.children[5].innerHTML = '<div class="input-group"><input type="text" class="form-control" value=""></div>';
    row.children[6].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value=""></div>';
    row.children[7].innerHTML = '<div class="input-group" style="width:70px"><input type="number" class="form-control" value="0"></div>';
    row.children[8].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value=""></div>';
    row.children[9].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value=""></div>';
    row.children[10].innerHTML = '<div class="form-check"><input class="form-check-input" type="checkbox" value=""></div>';

    row.children[11].innerHTML =    
        '<select class="form-select">' +
            '<option selected value="">No Service</option>' +
        '</select>'

    var serviceSelect = row.children[11].querySelector(".form-select");
    var services = DataMeta.admin.services;

    for (var i = 0; i < DataMeta.admin.services.length; i++) {
        var option = document.createElement("option")
        option.setAttribute('value', services[i].id.uuid);
        serviceSelect.appendChild(option);
        option.innerHTML = services[i].name;
    }

    row.children[12].innerHTML = '<div style="width:70px"><button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-success enabled" onclick="addMetaDatum(event);"><i class="bi bi-check2"></i></button>' +
                                 '<button type="button" class="py-0 px-1 mx-1 btn btn-sm btn-outline-danger enabled" onclick="DataMeta.admin.getMetadata();"><i class="bi bi-x"></i></button></div>'
}

// Saves the editing done for Metadata Settings
function saveMetaDatum(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // If the picture in the button was triggered instead of the button itself, change to the button element
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode.parentNode;

    var metadata_id = row.id;
    var name = row.children[0].querySelector('input').value;
    var regexDescription = row.children[1].querySelector('textarea').value;
    var longDescription = row.children[2].querySelector('textarea').value;
    var example = row.children[3].querySelector('input').value;
    var regExp = row.children[4].querySelector('input').value;
    var dateTimeFmt = row.children[5].querySelector('input').value;
    var isMandatory = row.children[6].querySelector('input').checked;
    var order = parseInt(row.children[7].querySelector('input').value);
    var isFile = row.children[8].querySelector('input').checked;
    var isSubmissionUnique = row.children[9].querySelector('input').checked;
    var isSiteUnique = row.children[10].querySelector('input').checked;
    var serviceId = row.children[11].querySelector('select').value;

    if(isNaN(order)) {
        showAlert("metadata_alert", "Please specify an int in the 'order' field.");
        return;
    }

    fetch(DataMeta.api('metadata/' + metadata_id),
    {
        method: 'PUT',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
            regexDescription,
            longDescription,
            example,
            regExp,
            dateTimeFmt,
            isMandatory,
            order,
            isFile,
            isSubmissionUnique,
            isSiteUnique,
            serviceId
        })
    })
    .then(function (response) {
        if(response.status == '200') {
            // Reload Metadata Table
            DataMeta.admin.getMetadata();

            // Remove any alerts there still are
            document.getElementById("metadata_alert").classList.remove("show");
        } else  if (response.status == "400") {
            response.json().then((json) => {
                showAlert("metadata_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("metadata_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("metadata_alert", "You do not have the rights to perform this action.");
        } else if (response.status == "404") {
            showAlert("metadata_alert", "The service you wanted to assign does not exist.");
        } else {
            showAlert("metadata_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// Creates a new Service
DataMeta.admin.newService = function() {
    var name = document.getElementById('service_label').value;

    fetch(DataMeta.api('services'),
    {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
        })
    })
    .then(function (response) {
        if(response.status == '200') {
            // Reload Metadata Table
            DataMeta.admin.getServices();

            // Remove any alerts there still are
            document.getElementById("services_alert").classList.remove("show");

            // Remove Label
            document.getElementById('service_label').value = "";
        } else  if (response.status == "400") {
            response.json().then((json) => {
                showAlert("services_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("services_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("services_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("services_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

function addMetaDatum(event) {

    // The button that triggered the function call
    var button = event.srcElement;

    // If the picture in the button was triggered instead of the button itself, change to the button element
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var row = button.parentNode.parentNode.parentNode;

    var name = row.children[0].querySelector('input').value;
    var regexDescription = row.children[1].querySelector('textarea').value;
    var longDescription = row.children[2].querySelector('textarea').value;
    var example = row.children[3].querySelector('input').value;
    var regExp = row.children[4].querySelector('input').value;
    var dateTimeFmt = row.children[5].querySelector('input').value;
    var isMandatory = row.children[6].querySelector('input').checked;
    var order = parseInt(row.children[7].querySelector('input').value);
    var isFile = row.children[8].querySelector('input').checked;
    var isSubmissionUnique = row.children[9].querySelector('input').checked;
    var isSiteUnique = row.children[10].querySelector('input').checked;
    var serviceId = row.children[11].querySelector('select').value;

    if(isNaN(order)) {
        showAlert("metadata_alert", "Please specify an int in the 'order' field.");
        return;
    }

    fetch(DataMeta.api('metadata'),
    {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
            regexDescription,
            longDescription,
            example,
            regExp,
            dateTimeFmt,
            isMandatory,
            order,
            isFile,
            isSubmissionUnique,
            isSiteUnique,
            serviceId
        })
    })
    .then(function (response) {
        if(response.status == '200') {
            // Reload Metadata Table
            DataMeta.admin.getMetadata();

            // Remove any alerts there still are
            document.getElementById("metadata_alert").classList.remove("show");
        } else  if (response.status == "400") {
            response.json().then((json) => {
                showAlert("metadata_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("metadata_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("metadata_alert", "You do not have the rights to perform this action.");
        } else if (response.status == "404") {
            showAlert("metadata_alert", "The service you wanted to assign does not exist.");
        } else {
            showAlert("metadata_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
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
            DataMeta.admin.updateUser(row.id, undefined, undefined, false, undefined, undefined, undefined);
        }
    } else {
        if(confirm("Do you want to make the user " + name + " admin of " + group + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, true, undefined, undefined, undefined);
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
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, false, undefined, undefined);
        }
    } else {
        if(confirm("Do you want to make the user " + name + " site admin?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, true, undefined, undefined);
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
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, undefined, false, undefined);
        }
    } else {
        if(confirm("Do you want to activate the user " + name + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, undefined, true, undefined);
        }
    }
}

/**
 * Toggles the site_read setting for a user
 */
 function toggleSiteRead(event) {

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
        if(confirm("Do you want to remove Site Read priviledges from the user " + name + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, undefined, undefined, false);
        }
    } else {
        if(confirm("Do you want to give Site Read priviledges to the user " + name + "?")) {
            DataMeta.admin.updateUser(row.id, undefined, undefined, undefined, undefined, undefined, true);
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

    cell.innerHTML =    '<div class="input-group" style="width:100%"><span class="input-group-text">' +
                        '<i class="bi bi-person-circle"></i>' +
                        '</span>' +
                        '<input name="fullname" type="text" aria-label="Full name" class="input_fullname form-control" value="' + name +'">' +
                        '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onClick="confirmUserNameChange(event, \'' + uuid + '\')"><i class="bi bi-check2"></i></button></div>';

    $('#table_users').DataTable().columns.adjust().draw("page");
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

    cell.innerHTML =    '<div class="input-group" style="width:100%"><span class="input-group-text">' +
                        '<i class="bi bi-building"></i>' +
                        '</span>' +
                        '<input name="fullname" type="text" aria-label="Full name" class="input_fullname form-control" value="' + name +'">' +
                        '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onClick="confirmGroupNameChange(event, \'' + uuid + '\')"><i class="bi bi-check2"></i></button></div>';

    $('#table_groups').DataTable().columns.adjust().draw("page");
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
    fetch(DataMeta.api('groups/' + group_id),
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
                showAlert("groups_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("groups_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("groups_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("groups_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// Adds a User with a specific ID to the service
DataMeta.admin.addServiceUser = function(uuid) {
    
    // Get the new user id
    var newUser = document.getElementById('user-id-input-' + uuid).value;

    // Get the ids of the current users of this service
    var userIds = [];
    DataMeta.admin.services.forEach((service) => {
        if(service.id.uuid == uuid) {
            service.userIds.forEach((userId) => {
                userIds.push(userId.uuid);
            })
        }
    });
    userIds.push(newUser);

    // Perform an update of the service with the new list of user ids
    DataMeta.admin.updateService(uuid, undefined, userIds);
}

// Enables editing of the Users of one Service
DataMeta.admin.editServiceUsers = function(event, uuid) {
    
    // The button that triggered the function call
    var button = event.srcElement;

    // Enable Editing
    button.parentNode.querySelectorAll('li').forEach((listElement) => {
        listElement.innerHTML = '<input class="form-check-input me-2" type="checkbox" value="" id="flexCheckDefault" checked>' + listElement.innerHTML;
    });

    // Rename Button && onclick()
    button.innerHTML = "Confirm edit";
    button.setAttribute('onclick', "DataMeta.admin.submitServiceUsersEdit(event, '" + uuid + "')");
}

// Enables editing of the Users of one Service
DataMeta.admin.submitServiceUsersEdit = function(event, uuid) {
    
    // The button that triggered the function call
    var button = event.srcElement;

    var userIds = []

    // Get List of checked users
    button.parentNode.querySelectorAll('li').forEach((listElement) => {
        var checkbox = listElement.querySelector('input[type="checkbox"]')

        if(checkbox.checked) {
            userIds.push(listElement.getAttribute('data-datameta-userid'));
        }
    });

    // Update the service with the new userId List
    DataMeta.admin.updateService(uuid, undefined, userIds);
}

// API call to change a service name
DataMeta.admin.updateService = function (service_id, name, userIds) {
    fetch(DataMeta.api('services/' + service_id),
    {
        method: 'PUT',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name,
            userIds
        })
    })
    .then(function (response) {
        if(response.status == '200') {
            // Reload Service Table
            DataMeta.admin.getServices();
        } else  if (response.status == "400") {
            response.json().then((json) => {
                showAlert("services_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("services_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("services_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("services_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

/**
 * Change the name of a service
 */
 function changeServiceName(event) {

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

    cell.innerHTML =    '<div class="input-group" style="width:100%"><span class="input-group-text">' +
                        '<i class="bi bi-gear"></i>' +
                        '</span>' +
                        '<input name="service_name" type="text" aria-label="Service name" class="input_fullname form-control" value="' + name +'">' +
                        '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-success enabled" onClick="confirmServiceNameChange(event, \'' + uuid + '\')"><i class="bi bi-check2"></i></button></div>';

    $('#table_services').DataTable().columns.adjust().draw();
}

//Confirms the ServiceNameChange and performs the api call
function confirmServiceNameChange(event, uuid) {
    var button = event.srcElement;

    // Change the location to the button if an element inside the button was clicked
    if(button.localName != "button") {
        button = button.parentNode;
    }

    var newName = button.parentNode.querySelector("input[name='service_name']").value;

    DataMeta.admin.updateService(uuid, newName, undefined);
}

// API call to get the AppSettings
DataMeta.admin.getAppSettings = function () {
    fetch(DataMeta.api('appsettings'),
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
        } else if (response.status == "400") {
            response.json().then((json) => {
                showAlert("site_alert", json.message);
            });
        } else if (response.status == "401") {
            showAlert("site_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("site_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("site_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// API call to get the Services
DataMeta.admin.getServices = function () {
    fetch(DataMeta.api('services'),
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
                DataMeta.admin.rebuildServicesTable(json);
                DataMeta.admin.services = json;
                // Remove any alerts there still are
                document.getElementById("services_alert").classList.remove("show");
            });
        } else if (response.status == "400") {
            response.json().then((json) => {
                showAlert("site_alert", json.message);
            });
        } else if (response.status == "401") {
            showAlert("site_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("site_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("site_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// API call get the Metadata definitions
DataMeta.admin.getMetadata = function () {
    fetch(DataMeta.api('metadata'),
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
                showAlert("metadata_alert", json.message);
            });
        } else if (response.status == "401") {
            showAlert("metadata_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("metadata_alert", "You do not have the rights to perform this action.");
        } else {
            showAlert("metadata_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

// Show alert boxes for a error messages in the individual tabs
function showAlert(alertName, text) {
    var al = document.getElementById(alertName);
    al.classList.remove("show");
    al.innerHTML = text + '<button type="button" class="btn-close" id="dismiss_' + alertName + '" onclick="DataMeta.admin.clearAlerts()"></button>';
    new bootstrap.Collapse(al, { show: true });
}

// API call to change user name, group, admin and enabled settings
DataMeta.admin.updateUser = function (id, name, groupId, groupAdmin, siteAdmin, enabled, siteRead) {
    fetch(DataMeta.api('users/' + id),
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
            enabled,
            siteRead
        })
    })
    .then(function (response) {
        if(response.status == '204') {
            // Reload Group, User & Request Tables
            DataMeta.admin.reload();
        } else if (response.status == "400") {
            response.json().then((json) => {
                showAlert("users_alert", json[0].message);
            });
        } else if (response.status == "401") {
            showAlert("users_alert", "You have to be logged in to perform this action.");
        } else if (response.status == "403") {
            showAlert("users_alert", "You do not have the rights to perform this action.");
        } else if (response.status == "404") {
            showAlert("users_alert", "The user or group you are referring to does not exist.");
        } else {
            showAlert("users_alert", "An unknown error occurred. Please try again later.");
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

DataMeta.admin.clearAlerts = function() {
    document.getElementById("groups_alert").classList.remove("show");
    document.getElementById("users_alert").classList.remove("show");
    document.getElementById("requests_alert").classList.remove("show");
    document.getElementById("site_alert").classList.remove("show");
    document.getElementById("metadata_alert").classList.remove("show");
    document.getElementById("services_alert").classList.remove("show");
}

window.addEventListener("dmready", function() {
    DataMeta.admin.initServicesTable();
    DataMeta.admin.initSiteTable();
    DataMeta.admin.initMetadataTable();
    DataMeta.admin.initUsersTable();
    DataMeta.admin.initGroupsTable();
    DataMeta.admin.reload();

    document.getElementById("nav-site-tab").addEventListener("click", DataMeta.admin.clearAlerts);
    document.getElementById("nav-metadata-tab").addEventListener("click", DataMeta.admin.clearAlerts);
    document.getElementById("nav-groups-tab").addEventListener("click", DataMeta.admin.clearAlerts);
    document.getElementById("nav-users-tab").addEventListener("click", DataMeta.admin.clearAlerts);
    document.getElementById("nav-requests-tab").addEventListener("click", DataMeta.admin.clearAlerts);
    document.getElementById("nav-services-tab").addEventListener("click", DataMeta.admin.clearAlerts);
});

window.addEventListener("load", function() {
    // Add listeners for "shown" events that re-draw() the datatables whenever
    // their respective tab is shown.
    document.getElementById("nav-users-tab").addEventListener("shown.bs.tab", function(event) {
        $("#table_users").DataTable().draw("page");
    });
    document.getElementById("nav-groups-tab").addEventListener("shown.bs.tab", function(event) {
        $("#table_groups").DataTable().draw("page");
    });
    document.getElementById("nav-metadata-tab").addEventListener("shown.bs.tab", function(event) {
        $("#table_metadata").DataTable().draw("page");
    });
    document.getElementById("nav-site-tab").addEventListener("shown.bs.tab", function(event) {
        $("#table_site").DataTable().draw("page");
    });
    document.getElementById("nav-services-tab").addEventListener("shown.bs.tab", function(event) {
        $("#table_services").DataTable().draw("page");
    });
});
