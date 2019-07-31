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

const piccanvas = document.getElementById('piccanvas');

var localStream;
var flag=false;
var context = piccanvas.getContext('2d');

var resultListHTML = "";

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

//Function to Start reading responses on button click
startrecordResponsesBTN.addEventListener('click', function(ev){
    init(); 
    console.log("We're in recordResponses");
    Result.html("Recording responses...");
    flag=true;
    processCapture();
    $("#stopRecordingBTN").show();
    $("#startrecordResponsesBTN").hide();
  ev.preventDefault();
  }, false);




// Success
function handleSuccess(stream) {
  window.stream = stream;
  video.srcObject = stream;
  localStream = stream;
}


  ///////////////////////////////function for stop recording button //////////////////////////////
stopRecordingBTN.addEventListener('click', function(ev1){
    currQnum = currQnum+1;
    
    //scanner.stop();
    if (Result.html()=='Recording responses...'){
    Result.html('');  
    }
    //stopping camera
    let stream = video.srcObject;
  let tracks = stream.getTracks();

  tracks.forEach(function(track) {
    track.stop();
  });

  video.srcObject = null;
  flag=false;

    /////


    submitResponseData();  

    $("#stopRecordingBTN").hide();
    $("#piccanvas").hide();
    console.log("this is the currqnum" + currQnum);
    var totalQCount = $('#questionListSize').val();
    
    console.log("this is the totalqount" + totalQCount);
    if (currQnum == parseInt(totalQCount)){
      $('#submitAndFinishBTN').show();
    }
    else{          
    $("#startAndNextBTN").show();
  }                 
    ev1.preventDefault();
  }, false);



function submitResponseData(){ 
  //var question_id = $('#questionID').val();
  var question_id =  $("#currrent_question_id").val();
   //window.alert(question_id);
  console.log('This is the current question_id');
  console.log(question_id);
  var formdataVal =  [];
  for(var a=0;a<resultArray.length;a++){
    formdataVal.push(question_id+':'+ resultArray[a]);
    console.log("here is the new tempVar value: " + formdataVal);
  }
  var formData = {formdataVal};
  formData  = JSON.stringify(formData);
  console.log("This is the form Data: "+formData);
 
  var responseForm = $("#responseForm").value;
 
  if(resultArray.length!=0){
    $.ajax({
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
  answerReceived = [];
}


function processCapture(){
  
   setInterval(function(){ 
     if(flag){
/////////////processing area
	  context.drawImage(video, 0, 0, 960, 720);
    var canvas = document.getElementById('piccanvas');
    var data = context.getImageData(0, 0, canvas.width, canvas.height);

    var t0 = Date.now();
    var codes = zbarProcessImageData(data);
    var t = Date.now() - t0;

    console.log('processing');

    if (codes.length === 0) {
      //codeType.textContent = 'N/A';
      console.log('not detected');
      //return;
    }
    else{
    for(var i=0;i<codes.length;i++)
    {
    var obj = codes[i][2];
    /////////////////
    var splitInput = obj.toString().split('@');
    if (answerReceived.includes(splitInput[0]))
    {
      //do nothing
    }
    else{
      answerReceived.push(splitInput[0]);
      resultArray.push(obj);                                            
    console.log("new value pushed to resultArray: " + obj);
    Result.html('Responses recorded for: <h3>'+ resultArray.length +'</h3> <ol>');
    for(var k=0;k<answerReceived.length;k++)
    {
      Result.append("<li name='responseListItems'><b>"+answerReceived[k]+"</b></li>");
      //hiddenInputList.append("<input type='text' name='resultInputListName' class='resultInputListClass'  value='"+ resultArray[k]+"'");
    }                
    Result.append("</ol>");
    }
///////////////////////    
    }    
  }
//end of processing area
  //processCapture();
     }
  }, 2000);
  
}