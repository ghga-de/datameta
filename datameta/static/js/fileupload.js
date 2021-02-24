'use strict';

function process_result_samplesheet(data) {
    DataMeta.submitRefresh();
    data.success.forEach(function(success){
        DataMeta.new_alert("<strong>Sample sheet '" + success.filename + "':</strong> " + success.n_added + " new records added.", "success");
    });
    data.errors.forEach(function(error){
        DataMeta.new_alert("<strong>Sample sheet '" + error.filename + "':</strong> " + error.reason, "danger");
    });
}

function process_result_data(json) {
    DataMeta.submitRefresh();
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

                        form.classList.add( 'is-uploading' );

                        if( isAdvancedUpload ) // ajax file upload for modern browsers
                        {
                            e.preventDefault();
                            e.stopPropagation();

                            // Create an array from the dropped FileList
                            var fileList = Array.from(droppedFiles);

                            // Dispatch event launching the first upload
                            var nextupload = new CustomEvent("nextupload", { detail : { files : fileList, form : form} });
                            document.dispatchEvent(nextupload);
                        }
                    });
            });

        document.addEventListener("nextupload", function(event) {
            var file = event.detail.files.pop();
            var form = event.detail.form;
            var ajaxData = new FormData();

            if (!file) {
                return;
            }
            ajaxData.set("ajax", 1);
            ajaxData.set("files[]", file);
            if (form.id=="form_data")
                ajaxData.set("action", "submit_data");
            else if (form.id=="form_samplesheets")
                ajaxData.set("action", "submit_samplesheet");

            var progress_bar;


            // ajax request
            var ajax = new XMLHttpRequest();
            ajax.open('POST', '/submit/action');

            ajax.onload = function()
            {
                if( ajax.status >= 200 && ajax.status < 400 )
                {
                    var data = JSON.parse( ajax.responseText );
                    if (form.id=="form_samplesheets") {
                        process_result_samplesheet(data);
                    } else if (form.id=="form_data") {
                        process_result_data(data);
                    }
                } else {
                    DataMeta.new_alert("<strong>The data submission failed.</strong> Please try again.", "danger")
                }

                // Dispatch for the next upload
                if (event.detail.files.length > 0) {
                    document.dispatchEvent(event);
                } else {
                    form.classList.remove( 'is-uploading' );
                    DataMeta.submitRefresh();
                }
            };

            ajax.upload.onprogress = function(event) {
                DataMeta.set_progress_bar(file.name, Math.ceil(100*event.loaded / event.total));
            }

            ajax.onerror = function()
            {
                form.classList.remove( 'is-uploading' );
                DataMeta.new_alert("<strong>The data submission failed.</strong> Please try again.", "danger")
                DataMeta.submitRefresh();
            };

            ajax.send( ajaxData );

        });

    }( document, window, 0 ));
