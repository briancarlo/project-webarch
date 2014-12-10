// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.


document.addEventListener('DOMContentLoaded', function () {
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    var current = tabs[0];
    url = current.url;
	console.log(url);
	document.getElementById('url').innerHTML = url;
	});
});

var x = document.getElementById('shortpath').value
console.log(x)



function saveChanges() {
        // Get a value saved in a form.
        var user = text.value;
        // Check that there's some code there.
        if (!theValue) {
          message('Error: No value specified');
          return;
        }
        // Save it using the Chrome extension storage API.
        chrome.storage.sync.set({'value': theValue}, function() {
          // Notify that we saved.
          message('Settings saved');
        });
      }





// Run our kitten generation script as soon as the document's DOM is ready.
// document.addEventListener('DOMContentLoaded', function () {
//   chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
//     console.log(tabs.url);
// });
// });
