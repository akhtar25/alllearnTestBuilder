


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


    //Code for editable table in fee management
    var $TABLE = $('#table');
var $BTN = $('#export-btn');
var $EXPORT = $('#export');

$('.table-add').click(function () {
var $clone = $TABLE.find('tr.hide').clone(true).removeClass('hide table-line');
$TABLE.find('table').append($clone);
});

$('.table-remove').click(function () {
$(this).parents('tr').detach();
});

$('.table-up').click(function () {
var $row = $(this).parents('tr');
if ($row.index() === 1) return; // Don't go above the header
$row.prev().before($row.get(0));
});

$('.table-down').click(function () {
var $row = $(this).parents('tr');
$row.next().after($row.get(0));
});

// A few jQuery helpers for exporting only
jQuery.fn.pop = [].pop;
jQuery.fn.shift = [].shift;

$BTN.click(function () {
var $rows = $TABLE.find('tr:not(:hidden)');
var headers = [];
var data = [];

// Get the headers (add special header logic here)
$($rows.shift()).find('th:not(:empty)').each(function () {
headers.push($(this).text().toLowerCase());
});

// Turn all existing rows into a loopable array
$rows.each(function () {
var $td = $(this).find('td');
var h = {};

// Use the headers from earlier to name our hash keys
headers.forEach(function (header, i) {
h[header] = $td.eq(i).text();
});

data.push(h);
});

// Output the result
$EXPORT.text(JSON.stringify(data));
});

<<<<<<< HEAD
$('#uploadDateInput').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 15 // Creates a dropdown of 15 years to control year
  });
=======
$('#courseDetailsButton').click(function(){    
    $('#classTrackerDiv').hide();
    $('#completeCourseDetailsDiv').show();
})

$('#closeCourseDetailsButton').click(function(){    
    $('#classTrackerDiv').show();
    $('#completeCourseDetailsDiv').hide();
})


//$("#startQuizButton").click(
 //   function () {
  //      document.getElementById('bg').src='{{ url_for('video_feed')}}';
   // });
>>>>>>> 56aee7e27caf6cfc9d0ae8aa1354c909f83f7f0f
