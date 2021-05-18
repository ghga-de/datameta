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

DataMeta.submit = {};
DataMeta.submit.unchecked = {};

"use strict";

DataMeta.submit.setLock = function(lock, uploadForm) {
    if (lock) {
        if (uploadForm) uploadForm.classList.add('is-uploading');
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
    btn.disabled = true;
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
    try{
        var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl)
        })
    } catch (error){
        console.log(error)
    }
}

/*
Refreshes the data displayed by the `submit` view
DEPRECATED
*/
DataMeta.submitRefresh = function() {
    alert("DataMeta.submitRefresh() is deprecated");
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

DataMeta.submit.buildKeyColunns = function(fileKeys, keys) {
    var columns = [];

    keys.forEach(function(key) {
        if (fileKeys.includes(key)) {
            /* FILE VALUES */
            columns.push({ title:key, data:null, render:function(metadataset) {
                var str = metadataset.record[key] === null ? '<span class="text-black-50"><i>empty</i></span>' : metadataset.record[key];
                return '<span data-datameta-class="field-status" data-datameta-uuid="'+metadataset.id.uuid+'" data-datameta-field="'+key+'">' +
                    '<i class="bi bi-hdd-rack-fill text-secondary" data-datameta-class="status-none" style="display:inline"></i>' +
                    '<i class="bi bi-hdd-rack-fill text-danger" data-datameta-class="status-err" style="display:none"></i>' +
                    '<i class="bi bi-hdd-rack-fill text-success" data-datameta-class="status-ok" style="display:none"></i> ' +
                    '</span>' +
                    str
            }});
        } else {
            /* NON-FILE VALUES */
            columns.push({ title:key, data:"record", render: function(record) {
                var str = record[key] === null ? '<span class="text-black-50"><i>empty</i></span>' : record[key];
                return str;
            }});
        }
    });

    return columns;
}

DataMeta.submit.statusColumn = { orderable:false, title:"", data:"id", render:function(data, type, row) {
    return '<span data-datameta-class="entity-status" data-datameta-uuid="'+data.uuid+'">' +
        '<i data-datameta-class="status-none" class="bi bi-question-circle-fill text-secondary" style="display:inline"></i>' + // Deselected
        '<i data-datameta-class="status-ok" class="bi bi-check-circle-fill text-success" style="display:none"></i>' + // OK
        '<a data-datameta-class="status-err" tabindex="0" role="button" data-bs-html="true" data-bs-toggle="popover" data-bs-trigger="focus" title="Validation Report" data-bs-content="" style="display:none"><i class="bi bi-exclamation-diamond-fill text-warning"></i></a>' + // ERROR
        '</span>';
}};

DataMeta.submit.rebuildMetadataTable = function(keys, fileKeys, metadata) {
    columns = [
        /* COLUMN 1: CHECKBOX */
        { orderable:false, title: "", data: null, render:function(data, type, row) {
                var checked = data.checked ? " checked" : "";
                return '<input class="form-check-input datameta-entity-check" type="checkbox" data-datameta-type="meta"  data-datameta-uuid="'+data.id.uuid+'"'+checked+'>';
        }},
        /* COLUMN 2: STATUS */
        DataMeta.submit.statusColumn
    ]
    columns = columns.concat(DataMeta.submit.buildKeyColunns(fileKeys, keys));
    /* COLUMN N+1: DELETE */
    columns.push({ orderable:false, title: "", data: "id", render:function(data, type, row) {
                return '<button type="button" class="py-0 px-1 btn btn-sm btn-outline-danger" data-datameta-class="btn-del-entity" data-datameta-type="mset" data-datameta-uuid="'+data.uuid+'"><i class="bi bi-trash-fill"></i></button>'
            }})
    $("#table_metadata").DataTable({
        drawCallback: function(settings) { DataMeta.submit.registerDynamicEvents(); },
        destroy: true,
        scrollX: true,
        data: metadata,
        sDom: "<'row'<'span8'l><'span8'f>r>t", // Hide footer
        order: [[2,"asc"]],
        paging : false,
        searching: false,
        columns: columns
    });
}

DataMeta.submit.showMetaErrors = function(metadata, errors) {
    if (!errors.length || !metadata.length) {
        return;
    }
    fetch(
        DataMeta.api("metadata"),
        { method : "GET" }
    ).then(function(response) {
        if (response.ok) return response.json()
        throw new Error();
    }).then(function(json) {
        var keys = json.filter(mdatum => mdatum.serviceId === null).map(metadatum => metadatum.name);
        var columns = [ DataMeta.submit.statusColumn ].concat(DataMeta.submit.buildKeyColunns([], keys));
        var card_failed = document.getElementById("card_failed");
        card_failed.classList.remove("d-none");
        $("#table_errors").DataTable({
            destroy: true,
            scrollX: true,
            data: metadata,
            sDom: "<'row'<'span8'l><'span8'f>r>t", // Hide footer
            order: [[1,"asc"]],
            paging : false,
            searching: false,
            columns: columns
        });
        DataMeta.submit.visualizeErrors(errors, false, card_failed);
    }).catch(function(error) {
        DataMeta.new_alert("<strong>ERROR</strong> An unknown error occurred when validating the submitted metadata. Please try again.", "danger")
        console.log(error);
    });
}

DataMeta.submit.visualizeErrors = function(errors, noselect, rootElement) {

    rootElement = rootElement ? rootElement : document;

    // Clear all errors
    Array.from(rootElement.querySelectorAll("[data-datameta-class='status-err'],[data-datameta-class='status-ok']")).forEach(elem => elem.style.display='none');
    Array.from(rootElement.querySelectorAll("[data-datameta-class='status-none']")).forEach(elem => elem.style.display='inline');
    Array.from(rootElement.querySelectorAll("[data-datameta-class='status-err']")).forEach(elem => elem.setAttribute("data-bs-content", " "));

    // Green-light all checked entities
    Array.from(rootElement.querySelectorAll("[data-datameta-class='entity-status']")).forEach(function(entity_status) {
        var uuid = entity_status.getAttribute("data-datameta-uuid");
        if (rootElement.querySelector("input[data-datameta-uuid='"+uuid+"']:checked")) {
            entity_status.querySelector("[data-datameta-class='status-none']").style.display="none";
            entity_status.querySelector("[data-datameta-class='status-ok']").style.display="inline";
        }
    });
    Array.from(rootElement.querySelectorAll("[data-datameta-class='field-status']"))
        .forEach(elem => {
            var uuid = elem.getAttribute("data-datameta-uuid");
            if (rootElement.querySelector("input[data-datameta-uuid='"+uuid+"']:checked")) {
                elem.querySelector("[data-datameta-class='status-none']").style.display="none";
                elem.querySelector("[data-datameta-class='status-ok']").style.display="inline";
            }
        });

    if (errors.length || noselect) {
        document.getElementById("commit_btn").style.display="none";
        document.getElementById("commit_label").style.display="none";
    } else {
        document.getElementById("commit_btn").style.display="block";
        document.getElementById("commit_label").style.display="block";
    }

    errors.forEach(function(error) {
        var uuid = error.entity.uuid;
        // Find the corresponding entity-status element
        var selector = "span[data-datameta-class='entity-status'][data-datameta-uuid='"+uuid+"']"
        var entity_status = rootElement.querySelector(selector);
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
            Array.from(rootElement.querySelectorAll("[data-datameta-class='field-status'][data-datameta-field='"+error.field+"'][data-datameta-uuid='"+uuid+"']"))
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
    DataMeta.submit.setLock(true);
    DataMeta.submit.unchecked[event.target.getAttribute('data-datameta-uuid')] = ! event.target.checked;
    DataMeta.submit.submit(true);
    DataMeta.submit.setLock(false);
}

DataMeta.submit.submit = function(validateOnly) {
    // Collect UUIDs from checkboxes
    var file_uuids = Array.from(document.querySelectorAll("input.datameta-entity-check[data-datameta-type='file']:checked"), input => input.getAttribute("data-datameta-uuid"));
    var mset_uuids = Array.from(document.querySelectorAll("input.datameta-entity-check[data-datameta-type='meta']:checked"), input => input.getAttribute("data-datameta-uuid"));

    // Collect Label
    var label = document.querySelector("#commit_label").value; 

    if (!file_uuids.length && !mset_uuids.length) {
        DataMeta.submit.visualizeErrors([], true, document.getElementById("masterfset"))
        return;
    }

    var endpoint = validateOnly ? DataMeta.api("presubvalidation") : DataMeta.api("submissions");

    // Make 'presubvalidation' API call
    fetch(
        endpoint,
        {
            method : "POST", body:JSON.stringify({
                metadatasetIds : mset_uuids,
                fileIds : file_uuids,
                label: label
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }
    ).then(function(response) {
        if (response.ok) {
            if (validateOnly) {
                return DataMeta.submit.visualizeErrors([], false, document.getElementById("masterfset"));
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
                    DataMeta.submit.visualizeErrors(json, false, document.getElementById("masterfset"));
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
        // Reload metadata table
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

DataMeta.submit.renderMetadataHelp = function() {
    fetch(
        DataMeta.api("metadata"),
        {method:"GET"}
    ).then(function(response) {
        if (response.ok) return response.json();
        throw new Error();
    }).then(function(json) {
        html_chunks = json.filter(mdat => mdat.serviceId === null).map(function(metadatum) {
            var html='<li href="#" class="list-group-item list-group-item-action" aria-current="true" style="background-color:transparent"><div class="d-flex w-100 justify-content-between"><h6 class="mb-1 text-success"><strong>'
            html += metadatum.name
            html += '</strong></h6>';
            html += metadatum.isMandatory ? '<span>mandatory <i class="bi bi-exclamation-circle-fill"></i></span>' : '<span>optional <i class="bi bi-question-circle"></i></span>';
            html += '</div><div>';
            if (metadatum.longDescription) html += "<p>" + metadatum.longDescription + "</p>";
            html += "<h6>Value constraints:</h6>";
            var constraints = [];
            if (metadatum.regexDescription) constraints.push(metadatum.regexDescription);
            if (metadatum.dateTimeFmt) constraints.push('<i class="bi bi-clock"></i> This is a date / time field. In plain text sources it has to be specified as <tt>' + metadatum.dateTimeFmt + '</tt>.');
            if (metadatum.isSiteUnique) {
                constraints.push("The value has to be unique across the database.")
            } else if (metadatum.isSubmissionUnique) {
                constraints.push("The value has to be unique within a submission.")
            }
            if (metadatum.isFile) constraints.push('<i class="bi bi-hdd-rack-fill"></i> This value corresponds to a file. Specify a filename here and upload a file with the same file name.');

            if (!constraints.length) constraints = [ "<em>This is a free text field with no constraints</em>" ];
            html += "<small>" + constraints.join("<br/>") + "</small>";
            html += '</div></li>';
            return html;
        });
        document.getElementById('ul_metadata').innerHTML = html_chunks.join('\n');
    }).catch(function(error) {
        console.log("Failed to render metadata help");
    });
}

DataMeta.submit.checkBoxes = function(table, checked) {
    DataMeta.submit.setLock(true);
    var checkboxes = document.querySelectorAll("input.datameta-entity-check[data-datameta-type='"+ table +"']")
    checkboxes.forEach(function(box) {
        box.checked = checked;
        DataMeta.submit.unchecked[box.getAttribute('data-datameta-uuid')] = ! checked;
    })

    DataMeta.submit.submit(true);
    DataMeta.submit.setLock(false);
}

DataMeta.submit.deleteSelectedMeta = function() {

    DataMeta.submit.setLock(true);

    // Get checked metadatasets
    var metadatasetIds = Array.from(document.querySelectorAll("input.datameta-entity-check[data-datameta-type='meta']:checked"), input => input.getAttribute("data-datameta-uuid"));

    // Delete all checked metadatasets
    fetch(DataMeta.api('rpc/delete-metadatasets'),
    {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body:  JSON.stringify({metadatasetIds})
    }).then(function(response) {
        if (response.ok) {
            DataMeta.submit.refresh();
            DataMeta.submit.setLock(false);
            return;
        }

        if (response.status==400) throw new DataMeta.AnnotatedError(response)
        
        var message;

        if (response.status==401) {
            message = "Unauthenticated."
        } else if (response.status==403) {
            message = "Access denied."
        } else if (response.status==404) {
            message = "File not found."
        } else {
            message = "Unknown error."
        }

        throw new Error(message);
    }).catch(function(error) {
        if (error instanceof DataMeta.AnnotatedError) {
            error.json().then(function(json){
                DataMeta.new_alert("<strong>ERROR</strong> Deleting the records failed: " + json[0].message, "danger");
                console.log(error);
                DataMeta.submit.refresh();
                DataMeta.submit.setLock(false);
            });
        } else {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the records failed: " + error.message, "danger")
            console.log(error.message);
            DataMeta.submit.refresh();
            DataMeta.submit.setLock(false);
        }
    });
}

DataMeta.submit.deleteSelectedFiles = function() {
    
    DataMeta.submit.setLock(true);

    // Get checked files
    var fileIds = Array.from(document.querySelectorAll("input.datameta-entity-check[data-datameta-type='file']:checked"), input => input.getAttribute("data-datameta-uuid"));

    // Delete all checked files
    fetch(DataMeta.api('rpc/delete-files'),
    {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({fileIds})
    }).then(function(response) {
        if (response.ok) {
            DataMeta.submit.refresh();
            DataMeta.submit.setLock(false);
            return;
        }

        if (response.status==400) throw new DataMeta.AnnotatedError(response)
        
        var message;

        if (response.status==401) {
            message = "Unauthenticated."
        } else if (response.status==403) {
            message = "Access denied."
        } else if (response.status==404) {
            message = "File not found."
        } else {
            message = "Unknown error."
        }

        throw new Error(message);
    }).catch(function(error) {
        if (error instanceof DataMeta.AnnotatedError) {
            error.json().then(function(json){
                DataMeta.new_alert("<strong>ERROR</strong> Deleting the files failed: " + json[0].message, "danger");
                console.log(error);
                DataMeta.submit.refresh();
                DataMeta.submit.setLock(false);
            });
        } else {
            DataMeta.new_alert("<strong>ERROR</strong> Deleting the files failed: " + error.message, "danger")
            console.log(error.message);
            DataMeta.submit.refresh();
            DataMeta.submit.setLock(false);
        }
    });
}

window.addEventListener("load", function() {
    DataMeta.submit.renderMetadataHelp();
    DataMeta.submit.refresh();

    document.getElementById("commit_btn").addEventListener("click", function(event) {
        DataMeta.submit.submit();
    });

    document.getElementById("select_all_metadate_btn").addEventListener("click", function(event) {
        var table = "meta";
        DataMeta.submit.checkBoxes(table, true);
    });

    document.getElementById("deselect_all_metadata_btn").addEventListener("click", function(event) {
        var table = "meta";
        DataMeta.submit.checkBoxes(table, false);
    });

    document.getElementById("delete_selected_metadata_btn").addEventListener("click", function(event) {
        DataMeta.submit.deleteSelectedMeta();
    });

    document.getElementById("select_all_files_btn").addEventListener("click", function(event) {
        var table = "file";
        DataMeta.submit.checkBoxes(table, true);
    });

    document.getElementById("deselect_all_files_btn").addEventListener("click", function(event) {
        var table = "file";
        DataMeta.submit.checkBoxes(table, false);
    });

    document.getElementById("delete_selected_files_btn").addEventListener("click", function(event) {
        DataMeta.submit.deleteSelectedFiles();
    });

    document.getElementById("btn_close_card_failed").addEventListener("click", event => document.getElementById("card_failed").classList.add("d-none"));
    document.getElementById("dismiss_meta_help").addEventListener("click", event => $("#row_explain_meta").slideUp())
    document.getElementById("show_meta_help").addEventListener("click", event => $("#row_explain_meta").slideToggle())
});
