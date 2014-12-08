// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// chrome.browserAction.onClicked.addListener(function(tab) {
//   chrome.tabs.create({url:chrome.extension.getURL("tabs_api.html")});
// });


chrome.browserAction.onClicked.addListener(function(tab) { 
	chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
	    var currentUrl = tabs[0].url;
	    //alert(currentUrl);
	    //var currentUrl = tab.url;
	    //var newUrl = currentUrl + "?customparam=1"
	  	console.log(currentUrl);
	    //chrome.tabs.update({url:newUrl});
	    //document.querySelector('#nerpTest').innerHTML = 'test';
	    document.getElementById("nerpDiv").innerHTML = "test"
	});
});

// document.addEventListener('DOMContentLoaded', function () {
//   document.querySelector('#nerpTest').innerHTML = currentUrl;
// });
