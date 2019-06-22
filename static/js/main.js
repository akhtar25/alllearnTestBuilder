
///////////////////////////////////////////////////////////////////////

'use strict';

//initiate the time
var date1 = new Date();
var videoElement = document.querySelector('video');
var audioSelect = document.querySelector('select#audioSource');
var videoSelect = document.querySelector('select#videoSource');
var canvas = document.querySelector('#canvas');
var video= document.querySelector('#video');
var Result = $("#result_strip");
var resultArray = [];
//set this to true from an event handler to stop the execution
var cancelled = false;
var keepRecording = true;
//var dataUrl = "";

navigator.mediaDevices.enumerateDevices()
  .then(gotDevices).then(getStream).catch(handleError);

audioSelect.onchange = getStream;
videoSelect.onchange = getStream;

function gotDevices(deviceInfos) {
  for (var i = 0; i !== deviceInfos.length; ++i) {
    var deviceInfo = deviceInfos[i];
    var option = document.createElement('option');
    option.value = deviceInfo.deviceId;
    if (deviceInfo.kind === 'audioinput') {
      option.text = deviceInfo.label ||
        'microphone ' + (audioSelect.length + 1);
      audioSelect.appendChild(option);
    } else if (deviceInfo.kind === 'videoinput') {
      option.text = deviceInfo.label || 'camera ' +
        (videoSelect.length + 1);
      videoSelect.appendChild(option);
    } else {
      console.log('Found one other kind of source/device: ', deviceInfo);
    }
  }
}

function getStream() {
  if (window.stream) {
    window.stream.getTracks().forEach(function(track) {
      track.stop();
    });
  }
  var widthVideo = function(){
    if (window.innerWidth < 600){
      return window.innerWidth;
    }
    else{
      return 300;
    }
  };
   var heightVideo = function(){
    if (window.innerHeight < 800 && window.innerWidth < 600){
      return window.innerHeight;
    }
    else{
      return 250;
    }
  };
  var constraints = {
    audio: {
      deviceId: {exact: audioSelect.value}
    },
    video: {
      deviceId: {exact: videoSelect.value},
        width:widthVideo(),
        height:heightVideo()
    }
  };

  navigator.mediaDevices.getUserMedia(constraints).
    then(gotStream).catch(handleError);
}

function gotStream(stream) {
  window.stream = stream; // make stream available to console
  videoElement.srcObject = stream;
}

function handleError(error) {
  console.log('Error: ', error);
}


///////////////////////////////function to analyse the codes captured from camera //////////////////////////////
 function takepicture() {
   if (keepRecording) {

  var widthVideo = function(){
    if (window.innerWidth < 600){
      return window.innerWidth;
    }
    else{
      return 300;
    }
  };
   var heightVideo = function(){
    if (window.innerHeight < 800 && window.innerWidth < 600){
      return window.innerHeight;
    }
    else{
      return 250;
    }
  };
   var width = widthVideo();
   var height = heightVideo();
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d').drawImage(video, 0, 0, width, height);
    var dataUrl = canvas.toDataURL('image/jpg');
    if (dataUrl!=""){
    $.ajax({
    type: "POST",
    url: "/decodes",
    data: {
    imgBase64: dataUrl
    }
    }).done(function(data) {
        if(data =='NO BarCode Found'){
            console.log("Trying..")
        }
        else{
       
            var obj = JSON.parse(data);
            var i;
            //I'll have to make futher changes here to always load up unique count of codes recorded
            
            for(i=0; i<obj.length;i++){               
                if (resultArray.includes(obj[i].code)){
                    //do nothing
                }
                else{
                resultArray.push(obj[i].code);
                console.log("new value pushed to resultArray: " + obj[i].code);
                Result.html('Responses Recorded: <h3>'+ resultArray.length +'</h3> <ol>');
                for(var k=0;k<resultArray.length;k++)
                {
                  Result.append("<li><b>"+resultArray[k]+"</b></li>");
                }                
                Result.append("</ol>");
                
              }
            }            
            window.navigator.vibrate(200);              
                //ev.preventDefault();
        }

        //timeout section
        var interval = setTimeout(function(){

          var date2 = new Date();
          var diff = date2 - date1;
          if(diff > 100000){

              Result.html('Try Again : Time Out');
              clearTimeout(interval);
          }                       
      },2000);
      // end of timeout section
        
    })
        .fail(function(){
            console.log('Failed')
        });        
      }
      setTimeout(takepicture, 2000);
      //Result.append("<b>Response Recorded: </b>");
 }
  }

///////////////////////////////function to submit recorded data to DB //////////////////////////////
function submitResponseData(){
  for(var j=0;j<resultArray.length;j++){
    console.log("This is the result array: "+ resultArray[j]);
  }
  
  if(resultArray.length!=0){
    $.ajax({
      url: "/responseDBUpdate",
      type: "POST",
      data: resultArray,
      success: function(response) {
       //success actions list
       window.alert(response+" from flask");
        
      },
      error: function(xhr) {
        window.alert("error occurred while updating db for last question");
      }
    });
    resultArray=[];
  }
}


  ///////////////////////////////function for start recording button //////////////////////////////
  recordResponsesBTN.addEventListener('click', function(ev){ 
    window.alert("We're here in recordResponses");
    Result.html("Recording responses...");
    $("#stopRecordingBTN").show();
    $("#recordResponsesBTN").hide();

      takepicture();     

      ev.preventDefault();
      }, false);




///////////////////////////////function for stop recording button //////////////////////////////
      stopRecordingBTN.addEventListener('click', function(ev1){

        keepRecording = false;      
        Result.html(''); 
        submitResponseData();   
        $("#startAndNextBTN").show();
        $("#stopRecordingBTN").hide();     
        ev1.preventDefault();
      }, false);