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

DataMeta.submit = {};
DataMeta.submit.unchecked = {};

"use strict";

DataMeta.submit.setlock = function(lock) {
    if (lock) {
        document.getElementById('form_data').classList.add('is-uploading');
        document.getElementById('form_samplesheets').classList.add('is-uploading');
        document.getElementById("masterfset").disabled = true;
    } else {
        document.getElementById('form_data').classList.remove('is-uploading');
        document.getElementById('form_samplesheets').classList.remove('is-uploading');
        document.getElementById("masterfset").disabled = false;
    }
}

DataMeta.submit.deleteFile = function(uuid) {
    fetch(
        DataMeta.api("files/") + uuid,
        {
            method : "DELETE",
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(function(response) {
        if (response.ok) {
            return DataMeta.submit.refresh();
        } else if (response.status==401) {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the file failed: Unauthenticated.", "danger")
        } else if (response.status==403) {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the file failed: Access denied.", "danger")
        } else if (response.status==404) {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the file failed: File not found.", "danger")
        } else if (response.status==400) {
            response.json().then(json => {
                DataMeta.new_alert("<strong>ERROR</strong> Deleting the file failed: " + json[0].message, "danger")
            });
        } else {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the file failed: Unknown error.", "danger")
        }
        DataMeta.submit.refresh();
    }).catch(function(error) {
        DataMeta.new_alert("<strong>ERROR</strong> Deleting the file failed: Unknown error.", "danger")
    });
}

DataMeta.submit.deleteMset = function(uuid) {
    fetch(
        DataMeta.api("metadatasets/") + uuid,
        {
            method : "DELETE",
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(function(response) {
        if (response.ok) {
            return DataMeta.submit.refresh();
        } else if (response.status==401) {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the record failed: Unauthenticated.", "danger")
        } else if (response.status==403) {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the record failed: Access denied.", "danger")
        } else if (response.status==404) {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the record failed: Record not found.", "danger")
        } else if (response.status==400) {
            response.json().then(json => {
                DataMeta.new_alert("<strong>ERROR</strong> Deleting the record failed: " + json[0].message, "danger")
            });
        } else {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the record failed: Unknown error.", "danger")
        }
        DataMeta.submit.refresh();
    }).catch(function(error) {
        DataMeta.new_alert("<strong>ERROR</strong> Deleting the record failed: Unknown error.", "danger")
    });
}

DataMeta.submit.deleteEntityEvent = function(event) {
    var btn = event.target.closest("button");
    if (btn.getAttribute("data-datameta-type")=="mset") {
        DataMeta.submit.deleteMset(btn.getAttribute("data-datameta-uuid"));
    } else if (btn.getAttribute("data-datameta-type")=="file") {
        DataMeta.submit.deleteFile(btn.getAttribute("data-datameta-uuid"));
    }
}

DataMeta.submit.registerDynamicEvents = function() {
    // Register Delete metadataset buttons
    Array.from(document.querySelectorAll("[data-datameta-class='btn-del-entity']")).forEach(elem => {
        elem.addEventListener("click", DataMeta.submit.deleteEntityEvent)
    });
}

DataMeta.new_alert = function(message, color) {
    var alerts = document.getElementById("div_alerts");
    var div    = document.createElement("div");
    div.classList = "mb-2 alert alert-" + color + " alert-dismissible fade show";
    div.setAttribute("role", "alert");
    div.innerHTML = message;
    var button = document.createElement("button");
    button.classList = "btn-close";
    button.setAttribute("type", "button"); button.setAttribute("data-bs-dismiss", "alert");
    button.setAttribute("aria-label", "Close");
    div.appendChild(button);
    alerts.appendChild(div);
}

DataMeta.set_progress_bar = function(uuid, val, classes, text) {
    // Find the corresponding progress bar group
    var group = document.querySelector('[data-datameta-class="dm-progress"][data-datameta-uuid="'+uuid+'"]')
    // The target element may not be available due to async behavior, in that case we silently do nothing
    if (!group) return;

    if (val === null) {
        // DISABLE PROGRESS
        group.querySelector('.progress').style.display = 'none';
        group.querySelector('[data-datameta-class="dm-content"]').style.display = null;
    } else {
        // SHOW PROGRESS
        // Hide content
        group.querySelector('[data-datameta-class="dm-content"]').style.display = 'none';
        // Set progress bar classes
        var pbar = group.querySelector('.progress-bar');
        pbar.className = 'progress-bar progress-bar-striped progress-bar-animated '
        if (classes) pbar.className += classes;
        // Set progress bar value
        pbar.style.width = val + "%";
        pbar.setAttribute("aria-valuenow", val.toString());
        // Set progress bar text
        if (text) {
            pbar.innerHTML = text;
        } else { 
            pbar.innerHTML = "";
        }
        // Show progress bar
        group.querySelector('.progress').style.display = null;
    }
}

DataMeta.reloadPopovers = function() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    DataMeta.popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })
}

/*
Refreshes the data displayed by the `submit` view
DEPRECATED
*/
DataMeta.submitRefresh = function() {
    alert("DataMeta.submitRefresh() is deprectated");
}

DataMeta.delete_pending = function() {
    var xhr = new XMLHttpRequest();

    var data = new FormData();
    data.set("action", "delete_pending");

    xhr.onreadystatechange = function(){
        var error = false;
        if (xhr.readyState === 4){
            if (xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);
                error = !json.success;
            } else error = 1;
            if (error) DataMeta.new_alert("Deletion failed. Please try again.", "danger");
            DataMeta.submitRefresh();
            document.getElementById("del_pending_btn").disabled = false;
        }
    };

    xhr.open('POST', '/submit/action');
    xhr.send(data);
}

/*
 *****************************************************************************************************
 */

DataMeta.submit.rebuildFilesTable = function(files) {
    $("#table_unannotated").DataTable({
        drawCallback: function(settings) { DataMeta.submit.registerDynamicEvents(); },
        destroy: true,
        data: files,
        sDom: "<'row'<'span8'l><'span8'f>r>t", // Hide footer
        order: [[2, "asc"]],
        paging : false,
        searching: false,
        columns: [
            /* COLUMN 1: CHECKBOX */
            { orderable:false, title: "", data: null, render:function(data, type, row) {
                var checked = data.checked ? " checked" : "";
                return '<input class="form-check-input datameta-entity-check" type="checkbox" data-datameta-type="file" data-datameta-uuid="'+data.id.uuid+'"'+checked+'>';
            }},
            /* COLUMN 2: STATUS */
            { orderable:false, title:"", data:"id", render:function(data, type, row) {
                return '<span data-datameta-class="entity-status" data-datameta-uuid="'+data.uuid+'">' +
                    '<i data-datameta-class="status-none" class="bi bi-question-circle-fill text-secondary" style="display:inline"></i>' + // Deselected
                    '<i data-datameta-class="status-ok" class="bi bi-check-circle-fill text-success" style="display:none"></i>' + // OK
                    '<a data-datameta-class="status-err" tabindex="0" role="button" data-bs-html="true" data-bs-toggle="popover" data-bs-trigger="focus" title="Validation Report" data-bs-content="" style="display:none"><i class="bi bi-exclamation-diamond-fill text-warning"></i></a>' + // ERROR
                    '</span>';
            }},
            /* ATTRIBUTE COLUMNS */
            { title: "File ID", data: "id", render: function(data, type, row) { return data.site; }},
            { title: "Name", data: "name"},
            { title: "Size", data: "filesize", render : (data, type, row) => data < 0 ? 'unknown' : byteSize(data) },
            { title: "Checksum", data: null, render:function(data, type, row) {
                return '<div  data-datameta-class="dm-progress" data-datameta-uuid="'+data.id.uuid+'">'+
                    '<div data-datameta-class="dm-content">' + data.checksum + '</div>' +
                    '<div class="progress" style="display:none"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%"></div></div>' +
                    '</div>';
            }},
            /* COLUMN N: DELETE */
            { orderable:false, title: "", data: "id", render:function(data, type, row) {
                return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" data-datameta-class="btn-del-entity" data-datameta-type="file" data-datameta-uuid="'+data.uuid+'"><i class="bi bi-trash-fill"></i></button>'
            }},
        ]
    });
}

DataMeta.submit.rebuildMetadataTable = function(keys, fileKeys, metadata) {
    columns = [
        /* COLUMN 1: CHECKBOX */
        { orderable:false, title: "", data: null, render:function(data, type, row) {
                var checked = data.checked ? " checked" : "";
                return '<input class="form-check-input datameta-entity-check" type="checkbox" data-datameta-type="meta"  data-datameta-uuid="'+data.id.uuid+'"'+checked+'>';
        }},
        /* COLUMN 2: STATUS */
        { orderable:false, title:"", data:"id", render:function(data, type, row) {
        return '<span data-datameta-class="entity-status" data-datameta-uuid="'+data.uuid+'">' +
                '<i data-datameta-class="status-none" class="bi bi-question-circle-fill text-secondary" style="display:inline"></i>' + // Deselected
                '<i data-datameta-class="status-ok" class="bi bi-check-circle-fill text-success" style="display:none"></i>' + // OK
                '<a data-datameta-class="status-err" tabindex="0" role="button" data-bs-html="true" data-bs-toggle="popover" data-bs-trigger="focus" title="Validation Report" data-bs-content="" style="display:none"><i class="bi bi-exclamation-diamond-fill text-warning"></i></a>' + // ERROR
                '</span>';
        }}
    ]
    /* COLUMNS 3..N: MEDATATA */
    keys.forEach(function(key) {
        if (fileKeys.includes(key)) {
            /* FILE VALUES */
            columns.push({ title:key, data:null, render:function(metadataset) {
                return '<span data-datameta-class="field-status" data-datameta-uuid="'+metadataset.id.uuid+'" data-datameta-field="'+key+'">' +
                    '<i class="bi bi-hdd-rack-fill text-secondary" data-datameta-class="status-none" style="display:inline"></i>' +
                    '<i class="bi bi-hdd-rack-fill text-danger" data-datameta-class="status-err" style="display:none"></i>' +
                    '<i class="bi bi-hdd-rack-fill text-success" data-datameta-class="status-ok" style="display:none"></i> ' +
                    '</span>' +
                    metadataset.record[key]
            }});
        } else {
            /* NON-FILE VALUES */
            columns.push({ title:key, data:"record", render:(record=>record[key]) });
        }
    });
    /* COLUMN N+1: DELETE */
    columns.push({ orderable:false, title: "", data: "id", render:function(data, type, row) {
                return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" data-datameta-class="btn-del-entity" data-datameta-type="mset" data-datameta-uuid="'+data.uuid+'"><i class="bi bi-trash-fill"></i></button>'
            }})
    $("#table_metadata").DataTable({
        drawCallback: function(settings) { DataMeta.submit.registerDynamicEvents(); },
        destroy: true,
        data: metadata,
        sDom: "<'row'<'span8'l><'span8'f>r>t", // Hide footer
        order: [[2,"asc"]],
        paging : false,
        searching: false,
        columns: columns
    });
}

DataMeta.submit.visualizeErrors = function(errors, noselect) {

    // Clear all errors
    Array.from(document.querySelectorAll("[data-datameta-class='status-err'],[data-datameta-class='status-ok']")).forEach(elem => elem.style.display='none');
    Array.from(document.querySelectorAll("[data-datameta-class='status-none']")).forEach(elem => elem.style.display='inline');
    Array.from(document.querySelectorAll("[data-datameta-class='status-err']")).forEach(elem => elem.setAttribute("data-bs-content", " "));

    // Green-light all checked entities
    Array.from(document.querySelectorAll("[data-datameta-class='entity-status']")).forEach(function(entity_status) {
        var uuid = entity_status.getAttribute("data-datameta-uuid");
        if (document.querySelector("input[data-datameta-uuid='"+uuid+"']:checked")) {
            entity_status.querySelector("[data-datameta-class='status-none']").style.display="none";
            entity_status.querySelector("[data-datameta-class='status-ok']").style.display="inline";
        }
    });
    Array.from(document.querySelectorAll("[data-datameta-class='field-status']"))
        .forEach(elem => {
            var uuid = elem.getAttribute("data-datameta-uuid");
            if (document.querySelector("input[data-datameta-uuid='"+uuid+"']:checked")) {
                elem.querySelector("[data-datameta-class='status-none']").style.display="none";
                elem.querySelector("[data-datameta-class='status-ok']").style.display="inline";
            }
        });

    if (errors.length || noselect) {
        document.getElementById("commit_btn").style.display="none";
    } else {
        document.getElementById("commit_btn").style.display="block";
    }

    errors.forEach(function(error) {
        var uuid = error.entity.uuid;
        // Find the corresponding entity-status element
        var selector = "span[data-datameta-class='entity-status'][data-datameta-uuid='"+uuid+"']"
        var entity_status = document.querySelector(selector);
        // Deactivate none field
        entity_status.querySelector("[data-datameta-class='status-none']").style.display="none";
        entity_status.querySelector("[data-datameta-class='status-ok']").style.display="none";
        // Enable error field
        var entity_err = entity_status.querySelector("[data-datameta-class='status-err']")
        entity_err.style.display="inline";
        // Add message
        var message = ""
        if (error.field) message += "<strong>" + error.field + "</strong><br/>";
        message += error.message + "<br/><br/>";
        entity_err.setAttribute("data-bs-content", entity_err.getAttribute("data-bs-content") + message);

        // If we have a field, try to toggle the corresponding field indicator
        if (error.field) {
            Array.from(document.querySelectorAll("[data-datameta-class='field-status'][data-datameta-field='"+error.field+"'][data-datameta-uuid='"+uuid+"']"))
                .forEach(elem => {
                    elem.querySelector("[data-datameta-class='status-none']").style.display="none";
                    elem.querySelector("[data-datameta-class='status-ok']").style.display="none";
                    elem.querySelector("[data-datameta-class='status-err']").style.display="inline";
                });
        }
    });



    DataMeta.reloadPopovers();
}

DataMeta.submit.checkboxChange = function(event) {
    document.getElementById("masterfset").disabled = true;
    DataMeta.submit.unchecked[event.target.getAttribute('data-datameta-uuid')] = ! event.target.checked;
    DataMeta.submit.submit(true);
    document.getElementById("masterfset").disabled = false;
}

DataMeta.submit.submit = function(validateOnly) {
    // Collect UUIDs from checkboxes
    var file_uuids = Array.from(document.querySelectorAll("input.datameta-entity-check[data-datameta-type='file']:checked"), input => input.getAttribute("data-datameta-uuid"));
    var mset_uuids = Array.from(document.querySelectorAll("input.datameta-entity-check[data-datameta-type='meta']:checked"), input => input.getAttribute("data-datameta-uuid"));


    if (!file_uuids.length && !mset_uuids.length) {
        DataMeta.submit.visualizeErrors([], true)
        return;
    }

    var endpoint = validateOnly ? DataMeta.api("presubvalidation") : DataMeta.api("submissions");

    // Make 'presubvalidation' API call
    fetch(
        endpoint,
        {
            method : "POST", body:JSON.stringify({
                metadatasetIds : mset_uuids,
                fileIds : file_uuids
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(function(response) {
        if (response.ok) {
            if (validateOnly) {
                return DataMeta.submit.visualizeErrors([]);
            } else {
                return DataMeta.submit.refresh();
            }
        }
        if (response.status==400) throw new DataMeta.AnnotatedError(response, false);
        throw new Error();
    }).catch(function(error) {
        if (error instanceof DataMeta.AnnotatedError) {
            error.response.json().then(function(json){
                if (validateOnly){
                    DataMeta.submit.visualizeErrors(json);
                } else {
                    DataMeta.new_alert("<strong>Creating a new submission failed</strong> Please verify that your submission is valid.", "danger")
                    DataMeta.submit.refresh();
                }
            });
        } else {
            alert("unknown error");
        }
    })
}

DataMeta.submit.refresh = function() {
    // Get data to display from UI API
    fetch(
        "/api/ui/pending",
        {method:"GET"}
    ).then(function(response) {
        if (response.ok) return response.json();
        if (response.status==400) throw new DataMeta.AnnotatedError(request);
    }).then(function(json) {
        // Annotate checked information
        json.files.forEach(file => file.checked = ! DataMeta.submit.unchecked[file.id.uuid])
        json.metadatasets.forEach(mset => mset.checked = ! DataMeta.submit.unchecked[mset.id.uuid])
        // Reload files table
        DataMeta.submit.rebuildFilesTable(json.files);
        // Reload metadarta table
        DataMeta.submit.rebuildMetadataTable(json.metadataKeys, json.metadataKeysFiles, json.metadatasets);
        // Register listeners
        Array.from(document.querySelectorAll("input.datameta-entity-check"), elem => elem.addEventListener("change", DataMeta.submit.checkboxChange));
        // Run validation
        DataMeta.submit.submit(true);
    }).catch(function(error) {
        if (error instanceof DataMeta.AnnotatedError) {
            error.json().then(function(json){});
        } else {

        }
    });
}

window.addEventListener("load", function() {
    DataMeta.submit.refresh();

    document.getElementById("commit_btn").addEventListener("click", function(event) {
            DataMeta.submit.submit();
        });

    document.getElementById("del_pending_btn").addEventListener("click", function(event) {
            event.target.disabled = true;
            DataMeta.delete_pending();
        });
});

