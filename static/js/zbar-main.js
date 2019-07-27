'use strict';

var takePicture = document.getElementById("take-picture");
var canvas = document.createElement("canvas");
var codeType = document.getElementById("code-type");
var codeContent = document.getElementById("code-content");
var openUrlButton = document.getElementById("open-url");
var searchCodeButton = document.getElementById("search-code");
var Result = document.getElementById("result_strip");
const video = document.getElementById('video');
const piccanvas = document.getElementById('piccanvas');
const snap = document.getElementById("snap");
const errorMsgElement = document.querySelector('span#errorMsg');
var localStream;
var flag=false;
var context = piccanvas.getContext('2d');

const constraints = {
  audio: false,
  video: {
    width: 1280, height: 720
  }
};

// Access webcam
async function init() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    handleSuccess(stream);
  } catch (e) {
    errorMsgElement.innerHTML = `navigator.getUserMedia error:${e.toString()}`;
  }
}

// Success
function handleSuccess(stream) {
  window.stream = stream;
  video.srcObject = stream;
  localStream = stream;
}

// Load init
init();

stopCam.addEventListener("click", function() {
let stream = video.srcObject;
  let tracks = stream.getTracks();

  tracks.forEach(function(track) {
    track.stop();
  });

  video.srcObject = null;
  flag=false;
});

function scan() {
  if (typeof MozActivity !== 'undefined') {
    // in Firefox OS v1.0.1, input[file] does not work, using Web Activities
    takePictureUsingWebActivity();
    return;
  }

  takePicture.click();
}
function openUrl() {
  window.open(codeContent.value);
}
function searchCode() {
  window.open('https://www.google.com/search?q=' + codeContent.value);        
}

// https://hacks.mozilla.org/2013/01/introducing-web-activities/
function takePictureUsingWebActivity() {
  var pick = new MozActivity({
    name: "pick",
    data: { type: ["image/png", "image/jpg", "image/jpeg"] }
  });
  pick.onsuccess = function () {
    loadImage(URL.createObjectURL(this.result.blob));
  };
}

takePicture.onchange = function (event) {
  var files = event.target.files;
  if (!files || files.length === 0) {
    return;
  }

  var file = files[0];
  var imgURL = (window.URL || window.webkitURL).createObjectURL(file);
  loadImage(imgURL);
}

function loadImage(imgURL) {
  // clean
  codeType.textContent = '';
  codeContent.value = '';
  openUrlButton.setAttribute('hidden', 'hidden');
  searchCodeButton.setAttribute('hidden', 'hidden');

  var img = new Image();
  img.onload = function () {
    var canvas = document.createElement('canvas');
    // resizing image to 320x240 for slow devices
    var k = (320 + 240) / (img.width + img.height);
    canvas.width = Math.ceil(img.width * k);
    canvas.height = Math.ceil(img.height * k);
    var ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, img.width, img.height,
                  0, 0, canvas.width, canvas.height);

    var data = ctx.getImageData(0, 0, canvas.width, canvas.height);

    var t0 = Date.now();
    var codes = zbarProcessImageData(data);
    var t = Date.now() - t0;
    document.body.classList.remove('processing');

    if (codes.length === 0) {
      codeType.textContent = 'N/A';
      document.body.classList.add('not-detected');
      return;
    }
      
    var type = codes[0][0];
    var data = codes[0][2];
    // publishing data
    codeType.textContent = type;
    codeContent.value = data;

    var isUrl = /^(http|https|ftp|mailto):/.test(data);
    if (isUrl) {
      openUrlButton.removeAttribute('hidden');
    } else {
      searchCodeButton.removeAttribute('hidden');
    }
  };
  img.src = imgURL;
  document.body.classList.add('processing');
  document.body.classList.remove('not-detected');
  document.getElementById('info').removeAttribute('hidden');
};

codeContent.value = '';

setTimeout(scan, 500); // trying to start "scanning"

var canInstall = !!(navigator.mozApps && navigator.mozApps.install);
if (canInstall) {
  var installButton = document.getElementById('install');
  var manifestURL = installButton.href;
  var request = window.navigator.mozApps.checkInstalled(manifestURL);
  request.onsuccess = function(e) {
    if (request.result) {
      return;
    }

    // App is not installed
    installButton.removeAttribute('hidden');
    installButton.addEventListener('click', function (e) {
      var request = navigator.mozApps.install(manifestURL);
      request.onsuccess = function (e) {
        alert('Application installed');
      };
      e.preventDefault();
    }, false);
  };
}

snap.addEventListener("click", function() {
  flag=true;

  //alert(content);
  processCapture();
});

function processCapture(){
  if(flag){
  setTimeout(function(){ 
/////////////processing area
	context.drawImage(video, 0, 0, 640, 480);
var canvas = document.getElementById('piccanvas');
   var ctx=context;
    var data = ctx.getImageData(0, 0, canvas.width, canvas.height);

    var t0 = Date.now();
    var codes = zbarProcessImageData(data);
    var t = Date.now() - t0;

    window.alert('processing');

    if (codes.length === 0) {
      //codeType.textContent = 'N/A';
      window.alert('not detected');
      //return;
    }
    for(var i=0;i<codes.length;i++)
    {
    var data = codes[i][2];
    Result.append(data);
    }
    alert("Hello");
//end of processing area
  processCapture();
  }, 3000);
  }
}