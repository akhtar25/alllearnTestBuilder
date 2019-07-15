'use strict';
//initiate the time
var date1 = new Date();
var videoElement = document.querySelector('video');
var audioSelect = document.querySelector('select#audioSource');
var videoSelect = document.querySelector('select#videoSource');
var canvas = document.querySelector('#canvas');
var video= document.querySelector('#video');
var Result = $("#result_strip");
var hiddenInputList = $("#questionListSizeDiv");
var resultArray = [];
//set this to true from an event handler to stop the execution
var cancelled = false;
var keepRecording = true;
var currQnum = 0;
var answerReceived = [];

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
      return 600;
    }
  };
   var heightVideo = function(){
    if (window.innerHeight < 800 && window.innerWidth < 600){
      return window.innerHeight;
    }
    else{
      return 500;
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
            for(i=0; i<obj.length;i++){
                var splitInput = obj[i].code.toString().split('@');
                if (answerReceived.includes(splitInput[0]))
                {
                  //do nothing
                }
                else{
                  answerReceived.push(splitInput[0]);
                  resultArray.push(obj[i].code);                                            
                console.log("new value pushed to resultArray: " + obj[i].code);
                Result.html('Responses recorded for: <h3>'+ resultArray.length +'</h3> <ol>');
                for(var k=0;k<answerReceived.length;k++)
                {
                  Result.append("<li name='responseListItems'><b>"+answerReceived[k]+"</b></li>");
                  //hiddenInputList.append("<input type='text' name='resultInputListName' class='resultInputListClass'  value='"+ resultArray[k]+"'");
                }                
                Result.append("</ol>");
                }
            }            
            window.navigator.vibrate(200);              
                //ev.preventDefault();
        }
    })
        .fail(function(){
            console.log('Failed')
        });        
      }
      setTimeout(takepicture, 5000);
 }
  }
  var request = "";
///////////////////////////////function to submit recorded data to DB //////////////////////////////
function submitResponseData(){ 
  current_question_id = $('#current_question_id').val();
  var formdataVal =  [];
  for(var a=0;a<resultArray.length;a++){

    formdataVal.push(current_question_id+':'+ resultArray[a]);
    console.log("here is the new tempVar value: " + formdataVal);

  }
  var formData = {formdataVal};
  formData  = JSON.stringify(formData);
  console.log("This is the form Data: "+formData);
 
  var responseForm = $("#responseForm").value;
 
  if(resultArray.length!=0){
    request = $.ajax({
      url: "/responseDBUpdate",
      type: "POST",
      data: formData ,
      contentType: 'application/json;charset=UTF-8',
      cache:false,
      success: function(response) {
       //success actions list
       console.log(response+" from flask");        
      },
      error: function(xhr) {
        console.log("error occurred while updating db for last question");
      }
    });
    resultArray=[];
  }
}
  ///////////////////////////////function for start recording button //////////////////////////////
  recordResponsesBTN.addEventListener('click', function(ev){ 
    console.log("We're in recordResponses");
    Result.html("Recording responses...");
    $("#stopRecordingBTN").show();
    $("#recordResponsesBTN").hide();
      takepicture();     
      ev.preventDefault();
      }, false);

///////////////////////////////function for stop recording button //////////////////////////////
      stopRecordingBTN.addEventListener('click', function(ev1){
        currQnum = currQnum+1;
        keepRecording = false;      
        console.log("this is the result html"+Result);
        submitResponseData();   
        $("#stopRecordingBTN").hide();
        console.log("this is the currqnum" + currQnum);
        var totalQCount = $('#questionListSize').val();
        
        console.log("this is the totalqount" + totalQCount);

        if (currQnum == parseInt(totalQCount)){
          $('#submitAndFinishBTN').show()
        }
        else{
        $("#startAndNextBTN").show();
      }          
        Result.html('');
        ev1.preventDefault();
      }, false);