# Install instruction when using the remote container feature of vscode

The remote container feature allows to run the editors backend insight a docker container which is all setup for development.  

## Quickstart:
Clone this repository:  
```
git clone https://github.com/ghga-de/datameta.git
```

And open the created directory in vscode, for instance like that:  
```
code ./datameta
```

Install the remote develoment extension:
- click on the extensions symbol in the side bar
- search for `Remote Development` and install it

To reopen vscode inside the dev container:
- select `View > Command Palette` in the dropdown menu 
- then select (or type): `Remote-Containers: Reopen in Container`

If you are executing this for the first time, the containers will be set up via docker-compose. This might take some time.

## Developing inside the container:
Once the build succeeded, you will be able to use vscode as usual.
The workspace will be mounted at `/workspace`.

However, before you start, you have to first install datameta in edit mode. Just type in the terminal:  
```
dev_install
```  
(this will execute the script at `/workspace/docker/dev_install`)  
You only have to run this once (unless you re-build the container or want to re-install datameta).

Every time you would like to deploy datameta, just type:  
```
dev_launcher
```   
(this will execute the script at `/workspace/docker/dev_launcher`)  

The frontend should be available at http://localhost:8080/ in your browser.

## Configuration and further information:
Any configuration regarding the dev container environment can be found at `/.devcontainer`.

The environment includes a few useful vscode extensions out of the box. 
If you find a extension that might be of use to everybody, feel free to add it to the `/.devcontainer/devcontainer.json`.

For general information on this vscode feature please look [here](https://code.visualstudio.com/docs/remote/create-dev-container).
 