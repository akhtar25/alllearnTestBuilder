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

//This section is for the creating the listener
var result_strip = document.getElementById("result_strip");
var resultListHTML = "";
var answerReceived = [];
let scanner = new Instascan.Scanner({ video: document.getElementById('video') });

scanner.addListener('scan', function (obj) {
    resultListHTML += "<li>"+obj+"</li>";
    result_strip.innerHTML=resultListHTML;
    answerReceived.push(obj);
        //alert(content);///////////////////////

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
});
      

//Function to Start reading responses on button click
startrecordResponsesBTN.addEventListener('click', function(ev){ 
    console.log("We're in recordResponses");
    Result.html("Recording responses...");
    $("#stopRecordingBTN").show();
    $("#startrecordResponsesBTN").hide();

//reading responses starts here
      Instascan.Camera.getCameras().then(function (cameras) {
        if (cameras.length > 0) {
          scanner.start(cameras[0]);
        } else {
          console.error('No cameras found.');
        }
      }).catch(function (e) {
        console.error(e);
      });   
  ev.preventDefault();
  }, false);


  ///////////////////////////////function for stop recording button //////////////////////////////
stopRecordingBTN.addEventListener('click', function(ev1){
    currQnum = currQnum+1;
    
    scanner.stop();
    //Result.html('');  

    submitResponseData();  

    $("#stopRecordingBTN").hide();
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