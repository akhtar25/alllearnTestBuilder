function readMore(){
    $("#readMoreDiv").show();
    $("#readMoreBtn").hide();
}

$('#hiddenSearch').click(function(){
    console.log("we're here");
    $('#search-2').show();  
    $('#q').focus();  
    $('#hiddenSearch').hide();
    $('#nonSearchDiv').hide();
    $('#logoDiv').show();
})

$(document).ready(function(){
//window.alert("weh're here");
    $(".dropdown-trigger").dropdown();
    $('.slider').slider();

    });

    // if user leaves the form the width will go back to original state

    $("#q").focusout(function () {
        $('#search-2').hide();
        $('#hiddenSearch').show();
        $('#nonSearchDiv').show();
        //handle other nav elements visibility here
        //$('.search-hide').removeClass('hide');
    });


