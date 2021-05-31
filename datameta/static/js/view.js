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

DataMeta.view = {}

DataMeta.view.buildColumns = function(mdata) {
    return mdata.map(function(mdatum) {
        return {
            title : mdatum.serviceId === null ? mdatum.name : '<i class="bi bi-cpu"></i> '+mdatum.name,
            data : null,
            render : function(mdataset, type, row, meta) {
                // We don't have access
                if (!(mdatum.name in mdataset.record)) return '<i class="bi bi-lock-fill text-danger"></i>';
                // Special case NULL and service metadatum with access but not run yet
                if (mdataset.serviceExecutions !== null
                    && mdatum.name in mdataset.serviceExecutions
                    && mdataset.serviceExecutions[mdatum.name]===null)
                    return '<span class="text-black-50"><i class="bi bi-hourglass-split"></i> <i>pending</i></span>';
                // Special case NULL
                if (mdataset.record[mdatum.name] === null) return '<span class="text-black-50"><i>empty</i></span>';
                // Speical case file
                if (mdataset.fileIds[mdatum.name]) return '<a class="link-bare" href="' + DataMeta.api('rpc/get-file-url/'+mdataset.fileIds[mdatum.name].site) +'?redirect=true"><i class="bi bi-cloud-arrow-down-fill"></i> '+mdataset.record[mdatum.name]+'</a>';
                // All other cases
                return mdataset.record[mdatum.name];
            }
        };
    });
}

DataMeta.view.initTable = function() {

  // Fetch metadata information from the API
  fetch(
    DataMeta.api("metadata"), { method : 'GET' }
  ).then(function(response) {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error()
    }
  }).then(function(json) {
    // Extract field names from the metadata information
    var mdata = json;

    var columns = [
        { title: '<i class="bi bi-house-door"></i> Submission', data: null, className: "id_col", render: function(data) {
            var label = data.submissionLabel ? data.submissionLabel : '<span class="text-black-50"><i>empty</i></span>';
            return '<div> <div class="large-super">' + label + '</div><div class="text-accent small-sub">' + data.submissionId.site + '</div></div>'
        }},
        { title: '<i class="bi bi-house-door"></i> Submission Time', data: null, className: "id_col", render: function(data) {
            var d = moment(new Date(data.submissionDatetime));
            return '<div> <div class="large-super">' + d.format('YYYY-MM-DD HH:mm:ss') +
                '</div><div class="text-accent small-sub">' + 'GMT' + d.format('ZZ') + '</div></div>'
        }},
        { title: '<i class="bi bi-house-door"></i> User', data: null, className: "id_col", render: data =>
            '<div> <div class="large-super">'+data.userName+'</div><div class="text-accent small-sub">'+data.userId.site+'</div></div>'
        },
        { title: '<i class="bi bi-house-door"></i> Group', data: null, className: "id_col", render: data =>
            '<div> <div class="large-super">'+data.groupName+'</div><div class="text-accent small-sub">'+data.groupId.site+'</div></div>'
        },
        { title: '<i class="bi bi-house-door"></i> ID', data: "id.site", className: "id_col", render: data => '<span class="text-accent">' + data + '</span>'}
      ].concat(DataMeta.view.buildColumns(mdata))

    // Build table based on field names
    $('#table_view').DataTable({
      dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
      rowId: 'id.uuid',
      paging : true,
      lengthMenu: [ 10, 25, 50, 100 ],
      order: [[1, "desc"]],
      pageLength: 25,
      searching: true,
      processing: true,
      scrollX: true,
      ajax: {
        url: "/api/ui/view",
        type: "POST"
      },
      serverSide : true,
      columns : columns
    });
  }).catch(function(error) {
      alert("An unknown error occurred.")
  });

}

window.addEventListener("dmready", function() {
  DataMeta.view.initTable();
});
