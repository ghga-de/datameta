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

/*
 * Define DataMeta
 */

window.DataMeta       = {};
DataMeta.uilocal      = {};
DataMeta.user         = {};
DataMeta.toolTips     = [];
DataMeta.popoverList  = [];
DataMeta.api = path => "/api/v1/" + path;

DataMeta.AnnotatedError = function(response) {
  this.response = response;
  this.name = 'AnnotatedError';
}

/* Element.closest() polyfill */

if (!Element.prototype.matches) {
    Element.prototype.matches =
        Element.prototype.msMatchesSelector ||
        Element.prototype.webkitMatchesSelector;
}

if (!Element.prototype.closest) {
    Element.prototype.closest = function(s) {
        var el = this;

        do {
            if (Element.prototype.matches.call(el, s)) return el;
            el = el.parentElement || el.parentNode;
        } while (el !== null && el.nodeType === 1);
        return null;
    };
}

DataMeta.datatablesRedraw = function() {
    if (window.jQuery) {
        var settings = $.fn.dataTableSettings;

        for ( var i=0 ; i<settings.length ; i++ ) {
            settings[i].oInstance.fnDraw("page");
        }
    }
}

/***********************************************   MD5   *********************************************/
/**
 * Return a cryptojs WordArray given an arrayBuffer (elemtent 0). Also return
 * original arraylength contained within buffer (element 1)
 * Solution originally: https://groups.google.com/forum/#!msg/crypto-js/TOb92tcJlU0/Eq7VZ5tpi-QJ
 */

DataMeta.arrayBufferToWordArray = function(ab) {
    var i8a = new Uint8Array(ab);
    var a = [];

    for (var i = 0; i < i8a.length; i += 4) {
        a.push(i8a[i] << 24 | i8a[i + 1] << 16 | i8a[i + 2] << 8 | i8a[i + 3]);
    } // WordArrays are UTF8 by default


    var result = CryptoJS.lib.WordArray.create(a, i8a.length);
    return [result, i8a.length];
}

DataMeta.readChunked = function(file, chunkCallback, endCallback) {
    var fileSize = file.size;
    var offset = 0;
    var reader = new FileReader();

    reader.onload = function () {
        if (reader.error) {
            endCallback(reader.error || {});
            return;
        }

        var wordArrayRes = DataMeta.arrayBufferToWordArray(reader.result);
        offset += wordArrayRes[1]; // callback for handling read chunk

        chunkCallback(wordArrayRes[0], offset, fileSize);

        if (offset >= fileSize) {
            endCallback(null);
            return;
        }

        readNext();
    };

    reader.onerror = function (err) {
        endCallback(err || {});
    };

    function readNext() {
        // 10MB chunks
        var fileSlice = file.slice(offset, offset + 10 * 1024 * 1024);
        reader.readAsArrayBuffer(fileSlice);
    }

    readNext();
}

/**
 * Adapted from http://stackoverflow.com/questions/39112096
 * Takes a file object and optional callback progress function
 *
 * @param {File} file - Instance of a File class (subclass of Blob).
 * @param {function} cbProgress - Callback function on progress change. Accepts a 0-1 float value.
 * @returns {Promise} AJAX Promise object.
 */

DataMeta.getLargeMD5 = function(file, cbProgress) {
    return new Promise(function (resolve, reject) {
        // create algorithm for progressive hashing
        var md5 = CryptoJS.algo.MD5.create();
        DataMeta.readChunked(file, function (chunk, offs, total) {
            md5.update(chunk);

            if (cbProgress) {
                cbProgress(Math.round(offs / total * 100));
            }
        }, function (err) {
            if (err) {
                reject(err);
            } else {
                var hash = md5.finalize();
                var hashHex = hash.toString(CryptoJS.enc.Hex);
                resolve(hashHex);
            }
        });
    });
}

/**
 * Gets information about the logged in user: ids, name, email, admin status and group
 */
window.addEventListener("load", function() {
    fetch(DataMeta.api('rpc/whoami'),
    {
        method: 'GET'
    })
    .then(response => response.json())
    .then(function (json) {
        DataMeta.user = json;
        fetch(
            DataMeta.api('server'),
            { method: 'GET' }
        ).then(function(response) {
            return response.json();
        }).then(function (json_api) {
            DataMeta.version       = json_api.datametaVersion;
            DataMeta.apiVersion   = json_api.apiVersion;
            var event              = new Event('dmready')
            window.dispatchEvent(event);
        })
    })
    .catch((error) => {
        console.log(error);
    });
});
