function copyToClipboard(text) {
    return new Promise((resolve, reject) => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                resolve(text);
            }).catch(err => {
                reject(err);
            });
        } else {
            // Fallback: Create a hidden text area
            let textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";  // Avoid scrolling to bottom
            textArea.style.left = "-9999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                successful ? resolve(text) : reject('Fallback: Copying text was unsuccessful');
            } catch (err) {
                document.body.removeChild(textArea);
                reject(err);
            }
        }
    });
}

function fetchResponse(url, data, method = "POST", fmt = "text"){
    /*Call fetch with the given url, data, and method. Return the response as a promise.

    url: The url to fetch from
    data: The data object to send in the request body
    method: The method to use in the request
    fmt: The format to return the response as. Can be "text", "json", or "blob"
    */

    // Set headers
    let headers = {
        'Content-Type': 'application/json',
    }

    let payload = {
        method: method,
        headers: headers,
    }
    if (data instanceof FormData){
        payload.headers = {};
        payload.body = data;
    }else if (!["GET", "HEAD"].includes(method)){
        payload.body = JSON.stringify(data);
        // payload.credentials = 'include';
    }else{
        console.log("adding data to url", data);
        for (let [key, value] of Object.entries(data)){
            console.log("key", key, "value", value)
            if (url.includes("?")){
                url += "&";
            }else{
                url += "?";
            }
            url += key + "=" + value;
        }
        console.log("url", url);
    }

    console.log("Fetching: " + method + " " + url + " with payload: " + JSON.stringify(payload));

    // Fetch
    return new Promise((resolve, reject)=> {
        fetch(url, payload)
            .then(response => {
                if (!response.ok) {
                    console.log("response", response);
                    if (fmt === "result"){
                        reject(response)
                    }else {
                        response[fmt]().then(reject, () => {
                            reject(response.statusText)
                        });
                    }
                }else{
                    console.warn("response", response);
                    if (fmt === "result"){
                        resolve(response)
                    }else {
                        response[fmt]().then(resolve, reject);
                    }
                }
            }) // Return response as specified format
            .catch((error) => {
                console.error('Error:', error);
                reject(error);
            });
    })
}

class Route {
    /* A class for making easy requests to a specific url. */

    constructor(url, method = "POST", fmt = "text"){
        /*
        url: The url to make requests to
        method: The method to use in requests (POST, GET, PUT, PATCH, DELETE)
        fmt: The format to return the response as. Can be "text", "json", or "blob"

        Returns a proxy object that allows for easy chaining of requests.
        e.g.
        let api = new Route("http://localhost:8000");
        api.path.to.resource({"a": 5}); // makes a POST request to http://localhost:8000/path/to/resource with data {"a": 5} and token in header
         */
        this.url = url;
        this.method = method;
        this.fmt = fmt;

        // Bind functions
        this.fetch = this.fetch.bind(this);
        this.post = this.post.bind(this);
        this.get = this.get.bind(this);
        this.put = this.put.bind(this);
        this.patch = this.patch.bind(this);
        this.extend = this.extend.bind(this);

        this.proxy = new Proxy(this, {
            get: function(target, name){
                if(name in target){
                    return target[name];
                }
                return target.extend("/" + name);
            },
            apply: function(target, thisArg, argumentsList){
                return target.fetch(...argumentsList);
            }
        });
        return this.proxy;

    }
    extend(extension, method = null, fmt = null){
        return new Route(this.url + extension, method || this.method, fmt || this.fmt);
    }
    fetch(data, extension = "", method = null, fmt = null){
        return fetchResponse(this.url + extension, data, method || this.method, fmt || this.fmt);
    }
    post(data, extension = "", fmt = null){return this.fetch(data, extension, "POST", fmt)}
    get(data, extension = "", fmt = null){return this.fetch(data, extension, "GET", fmt)}
    put(data, extension = "", fmt = null){return this.fetch(data, extension, "PUT", fmt)}
    patch(data, extension = "", fmt = null){return this.fetch(data, extension, "PATCH", fmt)}
    delete(data, extension = "", fmt = null){return this.fetch(data, extension, "DELETE", fmt)}
}

class API extends Route{
    constructor(url = location.origin, method = "POST", fmt = "text") {
        super(url, method, fmt);
        this.fetch = this.fetch.bind(this);
        this.getPaths = this.getPaths.bind(this);
        this.paths = null;
        this.pathsPromise = this.getPaths();
    }
    getPaths(){
        this.pathsPromise = this.get({}, "/openapi.json", "json").then(data =>{
            this.paths = data.paths;
            return this.paths;
        })
        return this.pathsPromise;
    }
}


class APIRoute extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: inline-block;
                    border-radius: 5px;
                    background-color: #cfcfcf;
                    padding: 0px;
                    margin: 5px;
                    cursor: pointer;
                    width: 30vw;
                }
                header {

                    border-radius: 5px;
                    padding: 5px;
                    background-color: #c8dae0
                }
                .extendedHeader {
                    background-color: #c8dae0;
                }
                .info {
                    padding: 5px;
                }
                .route {
                    font-weight: bold;
                    border-radius: 5px;
                    padding: 5px 10px 5px 10px;
                    display: inline-block;
                }
                .orange {
                    background-color: #e8d5c5
                }
                .tag {
                    display: none;
                    border-radius: 5px;
                    background-color: #efefef;
                }
                .param {
                    display: inline-block;
                    border-radius: 5px;
                    width: 75px;
                }
                .hidden {
                    display: none;
                }
                #send {
                    float: right
                }
                .code {
                    background-color: black;
                    color: white;
                }
                .box {
                    padding: 10px;
                    margin: 5px;
                    border-radius: 5px;
                }
                .clearfix::after {
                    content: "";
                    clear: both;
                    display: table;
                }

            </style>
            <header>
                <b id="routeDiv" class="route"></b>
                <div id="extendedHeader" class="hidden" style="overflow: hidden">
                    <p id="summaryDiv" class="summary hidden"></p>
                    <pre id="docsDiv" class="docs"></pre>
                    <div id="tagsDiv"></div>
                    <a id="urlPreview"  target="_blank"></a>
                </div>
            </header>
            <div id="bodyDiv" class="body hidden">
                <div id="infoDiv" class="info" style="position:relative;display:flex;">
                    <div id="paramsDiv" style="flex: 35%"></div>
                    <div id="codePreview" class="code box" style="flex: 65%; overflow:auto;">
                        <p id="copy" style="float: right; margin:0px;">copy</p>
                        <div id="python">
                            <pre id="requestsPreview" class = "code">
This is a sample
to see how this looks
                            </pre>

                        </div>
                    </div>
                </div>

                <button id="send"></button>
            </div>


        `;
        this.setInfo = this.setInfo.bind(this);

        this.routeDiv = this.shadowRoot.getElementById("routeDiv");
        this.tagsDiv = this.shadowRoot.getElementById("tagsDiv");
        this.summaryDiv = this.shadowRoot.getElementById("summaryDiv");
        this.docsDiv = this.shadowRoot.getElementById("docsDiv");
        this.paramsDiv = this.shadowRoot.getElementById("paramsDiv");
        this.header = this.shadowRoot.querySelector("header");
        this.extendedHeader = this.shadowRoot.getElementById("extendedHeader");
        this.sendButton = this.shadowRoot.getElementById("send");
        this.bodyDiv = this.shadowRoot.getElementById("bodyDiv");
        this.urlPreview = this.shadowRoot.getElementById("urlPreview");
        this.requestsPreview = this.shadowRoot.getElementById("requestsPreview");
        this.requestsPreviewCopy = this.shadowRoot.getElementById("copy");
        this.requestsPreviewCopy.addEventListener("click", ()=>{
            let t = this.requestsPreview.innerText;
            // copy t to clipboard, then turn the this.requestsPreviewCopy text color green for 500ms then back to white
             // Copy text to clipboard
            copyToClipboard(t).then(() => {
                // Change text color to green
                this.requestsPreviewCopy.style.color = 'green';

                // Set a timeout to change the color back to white after 500ms
                setTimeout(() => {
                    this.requestsPreviewCopy.style.color = 'white';
                }, 500);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        })
        this.isForm = false;
        this.collapsed = true;
        this.collapse = this.collapse.bind(this);
        this.expand = this.expand.bind(this);
        this.toggle = this.toggle.bind(this);
        this.call = this.call.bind(this);

        this.getUrlPreview = this.getUrlPreview.bind(this);
    }

    collapse(){
        for (let el of [this.bodyDiv, this.extendedHeader]) {
            if (!el.classList.contains("hidden")) {
                el.classList.add("hidden")
            }
        }
        this.collapsed = true;
    }
    expand(){
        for (let el of [this.bodyDiv, this.extendedHeader]) {
            if (el.classList.contains("hidden")) {
                el.classList.remove("hidden")
            }
        }
        this.collapsed = false;
    }
    toggle(){
        (this.collapsed?this.expand:this.collapse)()
    }

    setInfo(route, info, playground){
        console.log(route, info)
        this.route = route;
        this.info = info;
        this.playground = playground;
        this.routeDiv.innerText = route;
        this.summaryDiv.innerText = info.summary;
        if (info.description) {
            this.docsDiv.innerText = info.description;
        }
        this.info.defaults = {}

        this.routeDiv.style.backgroundColor = (info.method==="GET")?"lightblue":"orange";
        this.header.style.backgroundColor = (info.method==="GET")?"#c8dae0":"#e8d5c5";
        for (let tag of info.tags){
            let tagDiv = document.createElement("div");
            tagDiv.classList.add("tag");
            tagDiv.innerText = tag;
            this.tagsDiv.appendChild(tagDiv);
        }
        let foundParams = false;
        if (info.parameters) {
            for (let param of info.parameters) {
                // add an input for each parameter
                foundParams = true;
                let paramDiv = document.createElement("div");
                let label = document.createElement("label");
                label.innerText = param.name + ": ";
                paramDiv.appendChild(label);
                let input = document.createElement("input");
                let defaultVal = "";
                if (param.schema && Object.keys(param.schema).includes("default")){
                    defaultVal = param.schema.default;
                }
                if (defaultVal){
                    this.info.defaults[param.name] = defaultVal
                }
                console.log(route, param.name, param, defaultVal, [true, false].includes(defaultVal))
                if (param.in === "form"){
                    this.isForm = true;
                }
                if (param.in === "form" && param.name === "file"){
                    input.type = "file";
                    // accept .zip files only
                    // when uploaded, turn green and show the filename
                    input.accept = ".zip";
                    input.addEventListener("change", ()=>{
                        if (input.files.length > 0){
                            // hide input and show filename and green checkmark
                            input.classList.add("hidden");
                            let filename = document.createElement("span");
                            filename.innerText = input.files[0].name;
                            filename.style.color = "green";
                            filename.style.fontWeight = "bold";
                            filename.style.verticalAlign = "middle";
                            input.parentNode.insertBefore(filename, input.nextElementSibling);

                        }
                    })


                }else if ([true, false].includes(defaultVal)){
                    input.type = "checkbox";
                    input.checked = defaultVal;
                }else if (defaultVal && !isNaN(defaultVal)) {
                    input.type = "number";
                    input.value = defaultVal;
                }else{
                    input.type = "text";
                    input.value = defaultVal;
                }

                input.classList.add("param");
                input.addEventListener("keyup", this.getUrlPreview)
                input.addEventListener("change", this.getUrlPreview)
                paramDiv.appendChild(input);
                this.paramsDiv.appendChild(paramDiv);

            }
        }

        if (!foundParams){
            this.paramsDiv.classList.add("hidden")
        }

        this.header.addEventListener("click", ()=>{
            console.log(this.info)
            if (this.collapsed){
                this.playground.collapseAllExcept(this.route);
            }else{
                this.collapse()
            }

            // this.playground.leftPanel.scrollTop = this.offsetTop - 100;
        })
        this.sendButton.innerText = info.method;
        this.sendButton.addEventListener("click", ()=>{
            this.call();
        })
        this.routeDiv.addEventListener("click", (e)=>{
            this.playground.collapseAllExcept(this.collapsed?null:this.route);
            this.call();
            e.stopPropagation();
        })
        this.getUrlPreview()
    }
    call(){
        playground.callMethod(this.route, this.getParams());
    }
    getParams(){
        let params = {};
        for (let param of this.paramsDiv.querySelectorAll("input")){
            if (param.type === "checkbox"){
                params[param.previousSibling.innerText.slice(0, -2)] = param.checked;
            }else if (param.type === "file") {
                if (param.files.length > 0) {
                    params[param.previousSibling.innerText.slice(0, -2)] = param.files[0];
                }
            }else if (param.value) {
                params[param.previousSibling.innerText.slice(0, -2)] = param.value;
            }
        }
        if (this.isForm){
            let formData = new FormData();
            for (let [k, v] of Object.entries(params)){
                formData.append(k, v);
            }
            console.warn("form data", params, formData)
            params = formData;

        }
        return params;
    }
    setParams(params){
        for (let [k, v] of Object.entries(params)){
            for (let param of this.paramsDiv.querySelectorAll("input")){
                if (param.previousSibling.innerText.slice(0, -2) === k){
                    param.value = v;
                }
            }
        }
        this.getUrlPreview()
    }

    getUrlPreview(){
        let u = this.playground.url + this.route.replace("{path}", "");
        if (this.info.method === "GET"){
            let q = "?";
            let d = this.getParams();
            for (let [k, v] of Object.entries(d)){
                if (this.info.defaults[k] && this.info.defaults[k] == v){

                }else if (v){
                   if (q !== "?"){
                        q += "&"
                    }
                    q += `${k}=${v}`
                }
            }
            if (q !== "?") {
                u += q
            }
        }else{

        }
        this.urlPreview.href = u;
        this.urlPreview.innerText = u;
        this.getRequestsPreview()
    }

    getRequestsPreview(){
        let u = location.origin + this.route.replace("{path}", "");
        let d = this.getParams();
        let body = {}
        for (let [k, v] of Object.entries(d)) {
            if (!(this.info.defaults[k] && this.info.defaults[k] == v)) {
                body[k] = v;
            }
        }
        let j = JSON.stringify(body, null, 4);
        j = j.replaceAll(": false", ": False").replaceAll(": true", ": True")
        let r = 'import requests\n\nrequests.' + this.info.method.toLowerCase() + '(\n  "' + u + '",\n  ' + j + '\n).json()';
        this.requestsPreview.innerText = r;
    }
}


class APIPlayground extends HTMLElement {
    constructor() {
        super();
        this.url = location.origin;
        this.api = null;

        // bind functions
        this.onPaths = this.onPaths.bind(this);

        // insert html shadow dom
        this.attachShadow({mode: 'open'});
        this.shadowRoot.innerHTML = `
            <style>
                left-panel {
                  background-color: floralwhite;
                  max-width: 100%;
                  overflow-x: hidden;
                  overflow-y: scroll;
                }
                right-panel {
                    padding: 50px;
                    background-color: white;
                }
                .btn {
                  display: inline-block;
                  border-radius: 5px;
                }
                #docs {
                    display: none;
                }
                #urlContainer {
                    display: block;
                }
            </style>
            <panel-container>
                <left-panel id="leftpanel">
                     <a id="docs" href="${this.url}/docs" target="_blank">Docs</a><br/>
                      <div id="routes" style="max-height:90vh; overflow:auto">
                          <div id="getRoutes"></div>
                          <div id="postRoutes"></div>
                      </div>
                </left-panel>
                <right-panel id="rightpanel">
                    <div id="result"></div>
                    <div id="errors" style="color: orangered"></div>
                </right-panel>
            </panel-container>
        `;
        this.leftPanel = this.shadowRoot.getElementById("leftpanel");
        this.rightPanel = this.shadowRoot.getElementById("rightpanel");

        this.routeElements = {};
        this.routes = {};
        this.paths = null;

        this.convertToHTML = this.convertToHTML.bind(this);
        this.handleResult = this.handleResult.bind(this);
        this.handleError = this.handleError.bind(this);
        this.callMethod = this.callMethod.bind(this);
        this.callHash = this.callHash.bind(this);
        this.collapseAllExcept = this.collapseAllExcept.bind(this);
        this.setAPI = this.setAPI.bind(this);
        this.resetAPI = this.resetAPI.bind(this);
        this.onPaths = this.onPaths.bind(this);


        this.resetAPI(this.url);

        window.playground = this;


    }
    resetAPI(url){
        //remove all routes from routes dict
        for (let [route, element] of Object.entries(this.routeElements)){
            element.remove();
            delete this.routeElements[route];
        }
        for (let [route, info] of Object.entries(this.routes)){
            delete this.routes[route];
        }

        this.shadowRoot.getElementById("getRoutes").innerHTML = "";
        this.shadowRoot.getElementById("postRoutes").innerHTML = "";
        this.shadowRoot.getElementById("result").innerHTML = "";
        this.shadowRoot.getElementById("errors").innerText = "";
        this.paths = null;
        delete this.api;

        this.setAPI(url);
    }
    setAPI(url){
      this.url = url;
      this.api = new API(url);
      this.api.pathsPromise.then(this.onPaths);

      this.shadowRoot.getElementById("docs").href = url + "/docs";
  }

  callHash(){
    if (location.hash){
        try{
            let {route, data} = JSON.parse(atob(location.hash.slice(1)));
            this.collapseAllExcept(route);
            this.leftPanel.scrollTop = this.routeElements[route].offsetTop - 100;
            this.routeElements[route].setParams(data);
            if (this.routeElements[route].info.method.toLowerCase() === "get") {
                this.callMethod(route, data);
            }
        }catch (e){
            console.error(e)
        }
    }
  }
    callMethod(route, data){
        let info = this.paths[route];
        console.log(info);

        let hashData = {}
        for (let [k, v] of Object.entries(data)){
            if (!(v instanceof File)){
                hashData[k] = v;
            }
        }
        location.hash = btoa(JSON.stringify({route: route, data: hashData}));


        if (info.summary && info.summary.toLowerCase().includes("temporary redirect")){
            let u;
            if (route.includes("{path}")){
                let path = this.getParams().path;
                if (path && !path.startsWith('/')){
                    path = '/' + path;
                }
                u = this.url + route.replace("{path}", path) + "/";
            }else{
                u = this.url + route;
            }
            this.handleResult('<iframe src="' + u + '" style="width:100%; height: 95vh"/>')
        }else{
            let method = this.paths[route].method.toLowerCase();
            this.api[method](data, route, "result").then(this.convertToHTML).then(this.handleResult).catch(this.handleError);
        }
    }
    convertToHTML(result){
        let h = Object.fromEntries(result.headers.entries());
        console.log("h", h)


        if (h["content-type"] && h["content-type"].startsWith("image")){
            return result.blob().then(blob => {
                // Create an object URL for the blob
                const url = URL.createObjectURL(blob);

                // Create an img element
                const parent = document.createElement('div');
                const img = document.createElement('img');
                parent.appendChild(img);

                // Set the src of the img element
                img.src = url;
                img.style.width = "100%";
                img.style.maxHeight = "70vh";
                img.style.objectFit = "contain";
                return parent
            });
        }
        else if (["application/zip", "application/yaml"].includes(h["content-type"])) {
            // download the zip file
            return result.blob().then(blob => {
                // Create an object URL for the blob
                const url = URL.createObjectURL(blob);

                // Create an img element
                const parent = document.createElement('div');
                const a = document.createElement('a');
                parent.appendChild(a);

                const name = h["content-disposition"].split("filename=")[1].replaceAll('"', '');
                a.download = name;

                // Set the src of the img element
                a.href = url;
                a.innerText = name;
                a.style.width = "100%";
                a.style.maxHeight = "70vh";

                // now trigger the download
                a.click();

                return parent
            });
        }else{
            return result.text();
        }
    }
    handleResult(result){
        console.log("handling", result)
        if (result instanceof HTMLElement){
            this.shadowRoot.getElementById("result").innerHTML = "";
            this.shadowRoot.getElementById("result").appendChild(result);
        }else {
            this.shadowRoot.getElementById("result").innerHTML = result;
        }
        this.shadowRoot.getElementById("errors").innerText = "";
    }
    handleError(e){
        if (e instanceof Response){
            e.text().then(this.handleError);
            return;
        }
        if (e.startsWith && e.startsWith('{') && e.endsWith('}')){
            e = JSON.parse(e);
            if (e.detail && Object.keys(e).length === 1){
                e = e.detail;
            }else{
                e = JSON.stringify(e, null, 4);
            }
        }
        this.shadowRoot.getElementById("result").innerHTML = "";
        this.shadowRoot.getElementById("errors").innerText = e;
    }

    collapseAllExcept(exceptRoute){
        console.log(this, this.routeElements)
        for (let [r, e] of Object.entries(this.routeElements)){
            if (r === exceptRoute){
                e.expand()
            }else{
                e.collapse()
            }
        }
    }

  onPaths(paths){
        if (this.paths){
            throw "paths already set"
        }

      let getPaths = {};
      let postPaths = {};
      for (let [path, info] of Object.entries(paths)){
          if (!path.includes("favicon")) {
              if ("get" in info) {
                  getPaths[path] = info.get;
                  getPaths[path].method = "GET";
              }else if ("post" in info) {
                  postPaths[path] = info.post;
                  postPaths[path].method = "POST";
              }
          }
      }
      paths = {...getPaths, ...postPaths};
      this.paths = paths;


      for (let [path, info] of Object.entries(getPaths)){
            // make a pretty element for each path, show the path and the openapi info in a pretty way
            let div = document.createElement("api-route");
            div.setInfo(path, info, this);
            this.routeElements[path] = div;
            this.shadowRoot.getElementById("getRoutes").appendChild(div);
            this.shadowRoot.getElementById("getRoutes").appendChild(document.createElement("br"));
      }
      for (let [path, info] of Object.entries(postPaths)){
            // make a pretty element for each path, show the path and the openapi info in a pretty way
            let div = document.createElement("api-route");
            div.setInfo(path, info, this);
            this.routeElements[path] = div;
            this.shadowRoot.getElementById("postRoutes").appendChild(div);
            this.shadowRoot.getElementById("postRoutes").appendChild(document.createElement("br"));
      }

      this.callHash();
  }
}
customElements.define('api-playground', APIPlayground);
customElements.define('api-route', APIRoute);