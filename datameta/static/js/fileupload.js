'use strict';

function process_result_samplesheet(data) {
    DataMeta.submitRefresh();
    data.errors.missing_keys.forEach(function(missing){
        DataMeta.new_alert("<strong>Sample sheet '" + missing.filename + "':</strong> Ignored, missing columns: " + missing.keys.join(", "), "danger")
    });
    data.success.forEach(function(success){
        DataMeta.new_alert("<strong>Sample sheet '" + success.filename + "':</strong> " + success.n_added + " new records added.", "success")
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
                var input		 = form.querySelector( 'input[type="file"]' ),
                    label		 = form.querySelector( 'label' ),
                    errorMsg	 = form.querySelector( '.box__error span' ),
                    restart		 = form.querySelectorAll( '.box__restart' ),
                    droppedFiles = false,
                    showFiles	 = function( files ) {
                        label.textContent = files.length > 1 ? ( input.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', files.length ) : files[ 0 ].name;
                    },
                    triggerFormSubmit = function() {
                        var event = document.createEvent( 'HTMLEvents' );
                        event.initEvent( 'submit', true, false );
                        form.dispatchEvent( event );
                    };

                // letting the server side to know we are going to make an Ajax request
                var ajaxFlag = document.createElement( 'input' );
                ajaxFlag.setAttribute( 'type', 'hidden' );
                ajaxFlag.setAttribute( 'name', 'ajax' );
                ajaxFlag.setAttribute( 'value', 1 );
                form.appendChild( ajaxFlag );

                // automatically submit the form on file select
                input.addEventListener( 'change', function( e )
                    {
                        /* showFiles( e.target.files ); */
                        triggerFormSubmit();
                    });

                // drag&drop files if the feature is available
                if( isAdvancedUpload )
                {
                    form.classList.add( 'has-advanced-upload' ); // letting the CSS part to know drag&drop is supported by the browser

                    [ 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop' ].forEach( function( event )
                        {
                            form.addEventListener( event, function( e )
                                {
                                    // preventing the unwanted behaviours
                                    e.preventDefault();
                                    e.stopPropagation();
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
                            /* showFiles( droppedFiles ); */

                            triggerFormSubmit();
                        });
                }


                // if the form was submitted
                form.addEventListener( 'submit', function( e )
                    {
                        // preventing the duplicate submissions if the current one is in progress
                        if( form.classList.contains( 'is-uploading' ) ) return false;

                        form.classList.add( 'is-uploading' );
                        form.classList.remove( 'is-error' );

                        if( isAdvancedUpload ) // ajax file upload for modern browsers
                        {
                            e.preventDefault();
                            e.stopPropagation();
                            // gathering the form data
                            var formData = new FormData( form );
                            if( droppedFiles )
                            {
                                formData.delete(input.getAttribute( 'name' ));
                                Array.prototype.forEach.call( droppedFiles, function( file )
                                    {
                                        formData.append( input.getAttribute( 'name' ), file );
                                    });
                            }

                            // Separate the file list from the form data
                            var fileList = formData.getAll(input.getAttribute( 'name' ));

                            // Prepare an event carrying the file list and form data
                            var nextupload = new CustomEvent("nextupload", { detail : { formData : formData, files : fileList, form : form} });

                            document.dispatchEvent(nextupload);

                        }
                        else // fallback Ajax solution upload for older browsers
                        {
                            var iframeName	= 'uploadiframe' + new Date().getTime(),
                                iframe		= document.createElement( 'iframe' );

                            $iframe		= $( '<iframe name="' + iframeName + '" style="display: none;"></iframe>' );

                            iframe.setAttribute( 'name', iframeName );
                            iframe.style.display = 'none';

                            document.body.appendChild( iframe );
                            form.setAttribute( 'target', iframeName );

                            iframe.addEventListener( 'load', function()
                                {
                                    var data = JSON.parse( iframe.contentDocument.body.innerHTML );
                                    form.classList.remove( 'is-uploading' )
                                    form.classList.add( data.success == true ? 'is-success' : 'is-error' )
                                    form.removeAttribute( 'target' );
                                    if (form.id=="form_samplesheets") {
                                        process_result_samplesheet(data);
                                    } else if (form.id=="form_data") {
                                        process_result_data(data);
                                    }
                                });
                        }
                    });


                // restart the form if has a state of error/success
                Array.prototype.forEach.call( restart, function( entry )
                    {
                        entry.addEventListener( 'click', function( e )
                            {
                                e.preventDefault();
                                form.classList.remove( 'is-error', 'is-success' );
                                input.click();
                            });
                    });

                // Firefox focus bug fix for file input
                input.addEventListener( 'focus', function(){ input.classList.add( 'has-focus' ); });
                input.addEventListener( 'blur', function(){ input.classList.remove( 'has-focus' ); });

            });

        document.addEventListener("nextupload", function(event) {
            var file = event.detail.files.pop();
            var form = event.detail.form;
            var ajaxData = new FormData(form);

            if (!file) {
                return;
            }
            ajaxData.set("files[]", file);

            var progress_bar;


            // ajax request
            var ajax = new XMLHttpRequest();
            ajax.open( form.getAttribute( 'method' ), form.getAttribute( 'action' ), true );

            ajax.onload = function()
            {
                form.classList.remove( 'is-uploading' );
                if( ajax.status >= 200 && ajax.status < 400 )
                {
                    var data = JSON.parse( ajax.responseText );
                    /* form.classList.add( data.success == true ? 'is-success' : 'is-error' ); */
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
                }
            };

            ajax.upload.onprogress = function(event) {
                DataMeta.set_progress_bar(file.name, Math.ceil(100*event.loaded / event.total));
            }

            ajax.onerror = function()
            {
                form.classList.remove( 'is-uploading' );
                DataMeta.new_alert("<strong>The data submission failed.</strong> Please try again.", "danger")

                // Dispatch for the next upload
                if (event.detail.files.length > 0) {
                    // document.dispatchEvent(event);
                }
            };

            ajax.send( ajaxData );

        });

    }( document, window, 0 ));
