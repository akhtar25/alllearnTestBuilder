

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



 function takepicture() {
  if (cancelled) {
    return;
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
   var width = widthVideo();
   var height = heightVideo();
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d').drawImage(video, 0, 0, width, height);
    var dataUrl = canvas.toDataURL('image/jpg');
    $.ajax({
    type: "POST",
    url: "/decodes",
    data: {
    imgBase64: dataUrl
    }
    }).done(function(data) {
        if(data =='NO BarCode Found'){
          //new section
          
          //end of new section


            console.log("Trying..")
            var interval = setTimeout(function(){

                var date2 = new Date();
                var diff = date2 - date1;
                if(diff > 100000){

                    Result.html('Try Again : Time Out');
                    clearTimeout(interval);

                }
                //submitAndNextBTN
                //$('#startbutton').click();
                //$('#submitAndNextBTN').click();
                takepicture();
                if (resultArray.length==0){
                Result.html("Recording response...");                
              }
              //ev.preventDefault();

            },500);


        }
        else{
            // console.log(data.code);
            var obj = JSON.parse(data);
            var i;
            Result.html('<b>Response Recorded: </b><h3>'+ obj.length +'</h3> <ol>');
            for(i=0; i<obj.length;i++){
                Result.append("<li><b>"+obj[i].code+"</b></li>");
                resultArray.push(obj[i].code);
            }
            Result.append("</ol>")
            window.navigator.vibrate(200);
                takepicture();
                //Result.html("Recording response...");
                ev.preventDefault();
            //Call takepicture here too - done
            //Update this function to only keep running if cancelled is false
            //Create a separate click function associated with the same button to basically first stop the current 
            //run and then send the data to db
            //then it should start with the next run for the next question
        }

        // Do Any thing you want
        //if (!done) {
          // release control, so that handlers can be called, and continue in 10ms
         
        //}
    })
        .fail(function(){
            console.log('Failed')
        });
        setTimeout(takepicture, 10);
  }
  submitAndNextBTN.addEventListener('click', function(ev){ 
      cancelled = true;     
      dataUrl = "";    
      //if result has some value then send it to the db
      if(resultArray.length!=0){
        
        //var done = 1;
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
      cancelled = false;   
      takepicture();
      Result.html("Recording response...");
      ev.preventDefault();
      }, false);



      submitAndFinishBTN.addEventListener('click', function(ev1){

        cancelled = true;       
        dataUrl = "";  
      //if result has some value then send it to the db
      if(resultArray.length!=0){
        
        //var done = 1;
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

        ev1.preventDefault();
      }, false);