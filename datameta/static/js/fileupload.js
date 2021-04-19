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
#
# Modified from css-tricks.com
*/


'use strict';

function process_result_samplesheet(data) {
    DataMeta.submit.refresh();
    data.success.forEach(function(success){
        DataMeta.new_alert("<strong>Sample sheet '" + success.filename + "':</strong> " + success.n_added + " new records added.", "success");
    });
    data.errors.forEach(function(error){
        DataMeta.new_alert("<strong>Sample sheet '" + error.filename + "':</strong> " + error.reason, "danger");
    });
}

function process_result_data(json) {
    DataMeta.submit.refresh();
}

;( function ( document, window, index )
    {
        // feature detection for drag&drop upload
        var isAdvancedUpload = function()
        {
            var div = document.createElement( 'div' );
            return ( ( 'draggable' in div ) || ( 'ondragstart' in div && 'ondrop' in div ) ) && 'FormData' in window && 'FileReader' in window;
        }();


        // applying the effect for every form
        var forms = document.querySelectorAll( '.box' );
        Array.prototype.forEach.call( forms, function( form )
            {
                var droppedFiles = false;

                if( isAdvancedUpload )
                {
                    form.classList.add( 'has-advanced-upload' ); // letting the CSS part to know drag&drop is supported by the browser

                    [ 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop' ].forEach( function( event )
                        {
                            form.addEventListener( event, function( e )
                                {
                                    // preventing the unwanted behaviours
                                    e.preventDefault();
                                });
                        });
                    [ 'dragover', 'dragenter' ].forEach( function( event )
                        {
                            form.addEventListener( event, function()
                                {
                                    form.classList.add( 'is-dragover' );
                                });
                        });
                    [ 'dragleave', 'dragend', 'drop' ].forEach( function( event )
                        {
                            form.addEventListener( event, function()
                                {
                                    form.classList.remove( 'is-dragover' );
                                });
                        });
                    form.addEventListener( 'drop', function( e )
                        {
                            droppedFiles = e.dataTransfer.files; // the files that were dropped
                            if (form.id=="form_samplesheets" && droppedFiles.length > 1) {
                                DataMeta.new_alert("Please submit only one sample sheet at a time.", "danger")
                                return;
                            }
                            var event = new CustomEvent("dropsubmission");
                            form.dispatchEvent( event );
                        });
                } else {
                    alert('Your browser is not compatible with the file upload.');
                }


                // if the form was submitted
                form.addEventListener( "dropsubmission", function( e )
                    {
                        // preventing the duplicate submissions if the current one is in progress
                        if( form.classList.contains( 'is-uploading' ) ) return false;

                        DataMeta.submit.setLock(true, form);

                        if( isAdvancedUpload ) // ajax file upload for modern browsers
                        {
                            e.preventDefault();
                            e.stopPropagation();

                            // Create an array from the dropped FileList
                            var fileList = Array.from(droppedFiles);

                            // Dispatch event launching the first upload
                            if (form.id=="form_samplesheets") {
                                var nextupload = new CustomEvent("nextupload_samplesheet", { detail : { files : fileList, form : form} });
                                document.dispatchEvent(nextupload);
                            } else if (form.id=="form_data") {
                                var nextupload = new CustomEvent("nextupload_data", { detail : { files : fileList, form : form} });
                                document.dispatchEvent(nextupload);
                            } else {
                                DataMeta.submit.setLock(false);
                                console.log("Unknown drop target. Not uploading.");
                            }
                        }
                    });
            });

        document.addEventListener("nextupload_data", function(nextupload_event) {
            // Fetch the next file from the files array
            var file          = nextupload_event.detail.files.pop();
            // Store form for unlocking the form after the upload process finished
            var form          = nextupload_event.detail.form;

            // Insert row in table
            var dt = $('#table_unannotated').DataTable();
            var newRowId = dt.row.add({id : { uuid:"", site:"" }, name: file.name, filesize:-1, checksum:""}).pop()[0];
            var temp_uuid = "TEMP:"+newRowId;
            dt.row(newRowId).data({id : { uuid:temp_uuid, site:""}, name: file.name, filesize:-1, checksum:""}).draw();

            // Compute the file checksum
            DataMeta.getLargeMD5(file, function(val) {
                DataMeta.set_progress_bar(temp_uuid, val, "bg-warning", "Checksum");
            })
                .then(function(md5) {
                    DataMeta.set_progress_bar(temp_uuid, 0, "bg-success", "Upload");
                    // Request a new file upload
                    var POST_files = new FormData();
                    POST_files.append("name", file.name);
                    POST_files.append("checksum", md5);
                    fetch(DataMeta.api('files'), {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({name:file.name, checksum:md5})
                    })
                        .then(function(response){
                            if (response.ok) return response.json();
                            if (response.status==400) {
                                console.log(response.json());
                            }
                            throw new Error()
                        })
                        .then(function(data) {
                            // Update the files table
                            var uuid = data.id.uuid;
                            dt.row(newRowId).data({id : data.id, name: file.name, filesize:-1, checksum:md5, site_id:data.id.site_id}).draw("page");
                            // ### FILE UPLOAD ###
                            // Prepare multipart/form-data
                            var formData = new FormData();
                            formData.append("file", file);

                            var request = new XMLHttpRequest();
                            request.open("POST", data.urlToUpload);

                            // Set request headers
                            Object.entries(data.requestHeaders).forEach(([key, value]) => request.setRequestHeader(key, value));

                            // ON LOAD
                            request.onload = function() {
                                if(request.status==204) // According to docs this will also be what S3 returns. Confirm [!!] TODO
                                {
                                    // OK - Confirm the upload to the backend
                                    fetch(DataMeta.api('files/') + data.id.uuid, {
                                        method: "PUT",
                                        credentials: 'same-origin',
                                        headers: {
                                            'Content-Type': 'application/json'
                                        },
                                        body: JSON.stringify({contentUploaded:true})
                                    })
                                        .then(function(response){
                                            if (response.ok) return response.json();
                                            if (response.status==401) throw new Error("Unauthenticated");
                                            if (response.status==402) throw new Error("Unauthenticated");
                                            if (response.status==409) throw new Error("Checksum mismatch on data upload. Please try again.");
                                            if (response.status==400) throw new Error("Unexpected error");
                                            throw new Error("Unknown error");
                                        })
                                        .then(function(data){
                                            // We're done with this file. Proceed to the next or terminate upload procedure if none left.
                                            // Terminate current progress bar
                                            DataMeta.set_progress_bar(uuid, null);
                                            if (nextupload_event.detail.files.length > 0) {
                                                // Issue next upload
                                                document.dispatchEvent(nextupload_event);
                                            } else {
                                                DataMeta.submit.refresh();
                                                form.classList.remove('is-uploading');
                                                document.getElementById("masterfset").disabled = false;
                                            }
                                        })
                                        .catch(function(error){
                                            // An error occurred at PUT:/files/{id}
                                            DataMeta.submit.refresh();
                                            form.classList.remove( 'is-uploading' );
                                            document.getElementById("masterfset").disabled = false;
                                            DataMeta.new_alert("<strong>Confirming your file upload to the server failed.</strong> Please try again.", "danger")
                                            DataMeta.submit.refresh();
                                        });
                                } else {
                                    DataMeta.new_alert("<strong>The data submission failed.</strong> Please try again.", "danger")
                                }
                            };

                            // ON PROGRESS
                            request.upload.onprogress = function(progress_event) {
                                DataMeta.set_progress_bar(uuid, Math.ceil(100*progress_event.loaded / progress_event.total), "bg-success", "Upload");
                            };

                            request.upload.onload = function() {
                                // Upload finished, awaiting server-side checksum validation
                                DataMeta.set_progress_bar(uuid, 100, "bg-success", "Server-side processing");
                            }

                            // ON ERROR
                            request.onerror = function() {
                                // An error occurred at POST:{urlToUpload}
                                form.classList.remove( 'is-uploading' );
                                document.getElementById("masterfset").disabled = false;
                                DataMeta.new_alert("<strong>The data submission failed.</strong> Please try again.", "danger")
                                DataMeta.submit.refresh();
                            };

                            request.send(formData);
                        })
                        .catch(function(error){
                            // An error occurred at POST:/files
                            form.classList.remove( 'is-uploading' );
                            document.getElementById("masterfset").disabled = false;
                            DataMeta.new_alert("<strong>The pre-upload file announcement failed.</strong> Please try again.", "danger")
                            DataMeta.submit.refresh();
                        });
                });
        });

        document.addEventListener("mdata_upload", function(event) {
            if (event.detail.msets.length < 1) {
                event.detail.form.classList.remove( 'is-uploading' );
                document.getElementById("masterfset").disabled = false;
                DataMeta.submit.refresh();
                DataMeta.submit.showMetaErrors(event.detail.failed_msets, event.detail.errors);
                return;
            }

            var metadata = event.detail.msets.pop();

            fetch(DataMeta.api("metadatasets"), {
                method : 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({record:metadata})
            }).then(function(response) {
                if (response.ok) {
                    document.dispatchEvent(event);
                    return;
                }
                if (response.status==400) throw new DataMeta.AnnotatedError(response);
            }).catch(function(error) {
                if (error instanceof DataMeta.AnnotatedError) {
                    error.response.json().then(function(error_json) {
                        var fail_id = 'FAIL-' + event.detail.failed_msets.length;
                        metadata = { id : { uuid : fail_id }, record : metadata };
                        event.detail.failed_msets.push(metadata);
                        error_json = error_json.map(function(error) {
                            error.entity = metadata.id;
                            return error;
                        });
                        event.detail.errors = event.detail.errors.concat(error_json);
                        document.dispatchEvent(event);
                    }).catch(function(error) {
                        console.log("json parsing error", error);
                        document.dispatchEvent(event);
                    });
                } else {
                    console.log("Unknown error");
                    document.dispatchEvent(event);
                }
            });
        });

        document.addEventListener("nextupload_samplesheet", function(event) {
            var file = event.detail.files.pop();
            var form = event.detail.form;
            var formdata = new FormData();
            formdata.set("file", file)

            if (!file) {
                return;
            }

            fetch('/api/ui/convert', {
                method: "POST",
                credentials: 'same-origin',
                body: formdata
            }).then(function(response) {
                if (response.status==200) return response.json();
                if (response.status==400) throw new DataMeta.AnnotatedError(response);
                throw new Error();
            }).then(function(json) {
                var mdata_upload = new CustomEvent("mdata_upload", { detail : { msets : json , form : form, failed_msets : [], errors : []} });
                document.dispatchEvent(mdata_upload);
            }).catch(function(error) {
                if (error instanceof DataMeta.AnnotatedError) {
                    error.response.json().then(function(json) {
                        DataMeta.new_alert("<strong>Sample sheet upload failed:</strong> " + json[0].message, "danger")
                    });
                } else {
                    DataMeta.new_alert("<strong>Sample sheet upload failed:</strong> Unknown error.", "danger")
                }
                DataMeta.submit.setLock(false);
            });
        });
    }( document, window, 0 ));
