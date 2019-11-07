

  
function autocomplete(inp, arr) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;
    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) { return false;}
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items box z-depth-1");
        a.setAttribute("style", "position:absolute;z-index:1000;");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        /*for each item in the array...*/
        for (i = 0; i < arr.length; i++) {
          /*check if the item starts with the same letters as the text field value:*/
          if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
            /*create a DIV element for each matching element:*/
            b = document.createElement("DIV");
            /*make the matching letters bold:*/
            b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
            b.innerHTML += arr[i].substr(val.length);
            /*insert a input field that will hold the current array item's value:*/
            b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
            /*execute a function when someone clicks on the item value (DIV element):*/
            b.addEventListener("click", function(e) {
                /*insert the value for the autocomplete text field:*/
                inp.value = this.getElementsByTagName("input")[0].value;
                /*close the list of autocompleted values,
                (or any other open lists of autocompleted values:*/
                closeAllLists();
            });
            a.appendChild(b);
          }
        }
    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
          /*If the arrow DOWN key is pressed,
          increase the currentFocus variable:*/
          currentFocus++;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 38) { //up
          /*If the arrow UP key is pressed,
          decrease the currentFocus variable:*/
          currentFocus--;
          /*and and make the current item more visible:*/
          addActive(x);
        } else if (e.keyCode == 13) {
          /*If the ENTER key is pressed, prevent the form from being submitted,*/
          e.preventDefault();
          if (currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (x) x[currentFocus].click();
          }
        }
    });
    function addActive(x) {
      /*a function to classify an item as "active":*/
      if (!x) return false;
      /*start by removing the "active" class on all items:*/
      removeActive(x);
      if (currentFocus >= x.length) currentFocus = 0;
      if (currentFocus < 0) currentFocus = (x.length - 1);
      /*add class "autocomplete-active":*/
      x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
      /*a function to remove the "active" class from all autocomplete items:*/
      for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
      }
    }
    function closeAllLists(elmnt) {
      /*close all autocomplete lists in the document,
      except the one passed as an argument:*/
      var x = document.getElementsByClassName("autocomplete-items");
      for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i] && elmnt != inp) {
          x[i].parentNode.removeChild(x[i]);
        }
      }
    }
    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
  }
  
  /*An array containing all the country names in the world:*/
  //var countries = ["Afghanistan","Albania","Algeria","Andorra","Angola","Anguilla","Antigua & Barbuda","Argentina","Armenia","Aruba","Australia","Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bermuda","Bhutan","Bolivia","Bosnia & Herzegovina","Botswana","Brazil","British Virgin Islands","Brunei","Bulgaria","Burkina Faso","Burundi","Cambodia","Cameroon","Canada","Cape Verde","Cayman Islands","Central Arfrican Republic","Chad","Chile","China","Colombia","Congo","Cook Islands","Costa Rica","Cote D Ivoire","Croatia","Cuba","Curacao","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Ethiopia","Falkland Islands","Faroe Islands","Fiji","Finland","France","French Polynesia","French West Indies","Gabon","Gambia","Georgia","Germany","Ghana","Gibraltar","Greece","Greenland","Grenada","Guam","Guatemala","Guernsey","Guinea","Guinea Bissau","Guyana","Haiti","Honduras","Hong Kong","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Isle of Man","Israel","Italy","Jamaica","Japan","Jersey","Jordan","Kazakhstan","Kenya","Kiribati","Kosovo","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Macau","Macedonia","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta","Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova","Monaco","Mongolia","Montenegro","Montserrat","Morocco","Mozambique","Myanmar","Namibia","Nauro","Nepal","Netherlands","Netherlands Antilles","New Caledonia","New Zealand","Nicaragua","Niger","Nigeria","North Korea","Norway","Oman","Pakistan","Palau","Palestine","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Puerto Rico","Qatar","Reunion","Romania","Russia","Rwanda","Saint Pierre & Miquelon","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Korea","South Sudan","Spain","Sri Lanka","St Kitts & Nevis","St Lucia","St Vincent","Sudan","Suriname","Swaziland","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania","Thailand","Timor L'Este","Togo","Tonga","Trinidad & Tobago","Tunisia","Turkey","Turkmenistan","Turks & Caicos","Tuvalu","Uganda","Ukraine","United Arab Emirates","United Kingdom","United States of America","Uruguay","Uzbekistan","Vanuatu","Vatican City","Venezuela","Vietnam","Virgin Islands (US)","Yemen","Zambia","Zimbabwe"];

  var cities = ["Adoni","Amaravati","Anantapur","Chandragiri","Chittoor","Dowlaiswaram","Eluru","Guntur","Kadapa","Kakinada","Kurnool","Machilipatnam","Nagarjunakonda","Rajahmundry","Srikakulam","Tirupati","Vijayawda","Visakhapatnam","Vizianagaram","Yemmiganur","Itanagar","Dhuburi","Dibrugarh","Dispur","Guwahati","Jorhat","Nagaon","Sibsagar","Silchar","Tezpur","Tinsukia","Ara","Baruni","Begusarai","Bettiah","Bhagalur","Bihar Sharif","Bodh Gaya","Buxar","Chapra","Darbhanga","Dehri","Dinapur Nizamat","Gaya","Hajipur","Jamalpur","Katihar","Madhubani","Motihari","Munger","Muzaffarpur","Patna","Purnia","Pusa","Saharsa","Samastipur","Sasaram","Sitamarhi","Siwan","Chandigarh","Ambikapur","Bhilai","Bilaspur","Dhamtari","Durg","Jagdalpur","Raipur","Rajnandgaon","Silvassa","Daman","Diu","Delhi","New Delhi","Madgaon","Panaji","Ahmadabad","Amreli","Bharuch","Bhavnagar","Bhuj","Dwarka","Gandhinagar","Godhra","Jamnagar","Junagadh","Kandla","Khambhat","Kheda","Mahesana","Morvi","Nadiad","Navsari","Okha","Palnpur","Patan","Porbandar","Rajkot","Surat","Surendranagar","Valsad","Veraval","Ambala","Bhiwani","Chandigarh","Faridabad","Firozpur Jhirka","Gurgaon","Hansi","Hisar","Jind","Kaithal","Karnal","Kurukshetra","Panipat","Pehowa","Rewari","Rohtak","Sirsa","Sonipat","Bilaspur","Chamba","Dalhousie","Dharmshala","Hamirpur","Kangra","Kullu","Mand","Nahan","Shimla","Una","Anantnag","Baramula","Doda","Gulmarg","Jammu","Kathua","Leh","Punch","Rajauri","Srinagar","Udhampur","Bokaro","Chaibasa","Deoghar","Dhanbad","Dumka","Giridih","Hazaribag","Jamshedpur","Jaria","Rajmahal","Ranchi","Saraikela","Badami","Ballari","Bangalore","Belgavi","Bhadravati","Bidar","Chikkamagaluru","Chitradurga","Davangere","Halebid","Hassan","Hubballi-Dharwad","Kalaburagi","Kolar","Madikeri","Mandya","Mangaluru","Mysuru","Raichur","Shivamogga","Shravanabelagola","Shrirangapattana","Tumkuru","Alappuzha","Badagara","Idukki","Kannur","Kochi","Kollam","Kottayam","Kozhikode","Mattanheri","Palakkad","Thalassery","Thiruvananthapuram","Thrissur","Balaghat","Barwani","Betul","Bharhut","Bhind","Bhojpur","Bhopal","Burhanpur","Chhatarpur","Chhindwara","Damoh","Datia","Dewas","Dhar","Guna","Galior","Hoshangabad","Indore","Itarsi","Jabalpur","Jhabua","Khajuraho","Khandwa","Khargon","Maheshwar","Mandla","Mandsaur","Mhow","Morena","Murwara","Narsimhapur","Narsinghgarh","Narwar","Neemuch","Nowgon","Orchha","Panna","Raisen","Rajgarh","Ratlam","Rewa","Sagar","Sarangpur","Satna","Sehore","Seoni","Shahdol","Shajapur","Sheopur","Shivpuri","Ujjain","Vidisha","Ahmadnagar","Akola","Amravati","Aurangabad","Bhanara","Bhusawal","Bid","Buldana","Chandrapur","Daulatabad","Dhule","Jalgaon","Kalyan","Karli","Kolhapur","Mahabaleshwar","Malegaon","Matheran","Mumbai","Nagpur","Nanded","Nashik","Osmanabad","Pandharpur","Pabhani","Pune","Ratnagiri","Sangli","Satara","Sevagram","Solapur","Thane","Ulhasnagar","Vasai-Virar","Wardha","Yavatmal","Imphal","Cherrapunji","Shillong","Aizawl","Lunglei","Kohima","Mon","Phek","Wokha","Zunhboto","Balangir","Baleshwar","Baripada","Bhubaneshwar","Brahmapur","Cuttack","Dhenkanal","Keonjhar","Konark","Koraput","Paradip","Phulabani","Puri","Sambalpur","Udayagiri","Karaikal","Mahe","Puducherry","Yanam","Amritsar","Batala","Chandigarh","Faridkot","Firozpur","Gurdaspur","Hoshiarpur","Jalandhar","Kapurthala","Ludhiana","Nabha","Patiala","Rupnagar","Sangrur","Abu","Ajmer","Alwar","Amer","Barmer","Beawa","Bharatpur","Bhilwara","Bikaner","Bundi","Chittaurgarh","Churu","Dhaulpur","Dungarpur","Ganganagar","Hanumangarh","Jaipur","Jaisalmer","Jalor","Jhalawar","Jhunjhunu","Jodhpur","Kishangarh","Kota","Merta","Nagaur","Nathdwara","Pali","Phalodi","Pushkar","Sawai Madhopur","Shahpura","Sikar","Sirohi","Tonk","Udaipur","Gangtok","Gyalsing","Lachung","Mangan","Arcot","Chengalpattu","Chennai","Chidambaram","Coimbatore","Cuddalore","Dharmapuri","Dindigul","Erode","Kanhipuram","Kanniyakumari","Kodaikanal","Kumbakonam","Madurai","Mamallapuram","Nagappattinam","Nagercoil","Palayankottai","Pudukkottai","Rajapalaiyam","Ramanathapuram","Salem","Thanjavur","Tiruchcirappalli","Tirunelveli","Tiruppur","Tuticorin","Udhagamandalam","Vellore","Hyderabad","Karimnagar","Khammam","Mahbubnagar","Nizamabad","Sangareddi","Warangal","Agartala","Agra","Aligarh","Amroha","Aydhya","Azamgarh","Bahraich","Ballia","Banda","Bara Banki","Bareilly","Basti","Bijnor","Bithur","Budaun","Bulandshahr","Deoria","Etah","Etawah","Faizabad","Farrukhabad-cum-Fatehgarh","Fatehpur","Fatehpur Sikri","Ghaziabad","Ghazipur","Gonda","Gorakhpur","Hamirpur","Hardoi","Hathras","Jalaun","Jaunpur","Jhansi","Kannauj","Kanpur","Lakhimpur","Lalitpur","Lucknow","Mainpuri","Mathura","Meerut","Mirzapur-Vinhyachal","Moradabad","Muzaffarnagar","Partapgarh","Pilibhit","Prayagraj","Rae Bareli","Rampur","Saharanpur","Sambhal","Shahjahanpur","Sitapur","Sultanpur","Tehri","Varanasi","Almora","Dehra Dun","Haridwar","Mussoorie","Nainital","Pithoragarh","Alipore","Alipur Duar","Asansol","Baharampur","Bally","Balurghat","Bankura","Baranagar","Barasat","Barrackpore","Basirhat","Bhatpara","Bishnupur","Budge Budge","Burdwan","Chandernagore","Darjiling","Diamond Harbour","Dum Dum","Durgapur","Halisahar","Haora","Hugli","Ingraj Bazar","Jalpaiguri","Kalimpong","Kamarhati","Kanchrapara","Kharagpur","Koch Bihar","Kolkata","Krishnanagar","Malda","Midnapore","Murshidabad","Navadwip","Palashi","Panihati","Purulia","Raiganj","Santipur","Shantiniketan","Shrirampur","Siliguri","Siuri","Tamluk","Titagarh"]
  
  var states = ["Andaman and Nicobar Islands (union territory)","Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chandigarh (union territory)","Chhattisgarh","Dadra and Nagar Haveli (union territory)","Daman and Diu (union territory)","Delhi (NCR)","Goa","Gujarat","Haryana","Himachal Pradesh","Jammu and Kashmir","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Puducherry (union territory)","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand"]
  /*initiate the autocomplete function on the "myInput" element, and pass along the countries array as possible autocomplete values:*/
  autocomplete(document.getElementById("cityID"), cities);
  autocomplete(document.getElementById("stateID"), states);
  