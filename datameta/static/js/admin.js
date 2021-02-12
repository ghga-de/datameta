"use strict"; 

function fill_table(elem, data, keys) {
    data.forEach(function(datum, rnum) {
        var row = elem.insertRow(rnum);
        keys.forEach(function(key, cnum) {
            row.insertCell(cnum).innerHTML = datum[key];
        });
    });
}

function datameta_disable_user(uid) {
    console.log("disable user", uid);
}

function datameta_sudo_user(uid) {
    console.log("sudo user", uid);
}

function datameta_mod_user(uid) {
    console.log("mod user", uid);
}

function datameta_update_group_table(groups) {
    var tbody = document.getElementById("groups_tbody");
    tbody.innerHTML = "";
    fill_table(tbody, groups, ["id", "name"]);
}

function datameta_update_user_table(users) {
    var tbody = document.getElementById("users_tbody");
    tbody.innerHTML = "";
    fill_table(tbody, users, ["id", "fullname", "group_name", "email"]);
    for (var i = 0, row; row = tbody.rows[i]; i++) {
        var cell = row.cells[0]
        var uid = cell.innerHTML
        cell.innerHTML = "";
        var del = cell.appendChild(document.createElement("button"))
        var sudo = cell.appendChild(document.createElement("button"))
        var mod = cell.appendChild(document.createElement("button"))
        del.innerHTML = "Disable";
        sudo.innerHTML = "Sudo";
        mod.innerHTML = "Save";
        [del, sudo, mod].forEach(function(elem){
            elem.className = "btn btn-sm py-0"
        });
        del.className += " btn-outline-danger";
        sudo.className += " mx-1 btn-outline-danger";
        mod.className += " btn-outline-warning";

        del.addEventListener("click", function(x){datameta_disable_user(uid)});
        sudo.addEventListener("click", function(x){datameta_sudo_user(uid)});
        mod.addEventListener("click", function(x){datameta_mod_user(uid)});
    }
}

function datameta_update() {
    var xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function(){
        if (xhr.readyState === 4){
            var json = JSON.parse(xhr.responseText);
            datameta_update_user_table(json.users);
            datameta_update_group_table(json.groups);
        }
    };

    xhr.open('GET', '/admin.json');
    xhr.send();

}

window.addEventListener("load", function() {
    datameta_update();
});
