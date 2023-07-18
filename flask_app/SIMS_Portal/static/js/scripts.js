// fade flash alerts after 5 seconds
window.setTimeout(function() {
	$("#alert").fadeTo(500, 0) 
}, 6000);

$(function () {
  $('[data-toggle="tooltip"]').tooltip()
});

window.addEventListener('DOMContentLoaded', event => {

	// Navbar shrink function
	var navbarShrink = function () {
		const navbarCollapsible = document.body.querySelector('#mainNav');
		if (!navbarCollapsible) {
			return;
		}
		if (window.scrollY === 0) {
			navbarCollapsible.classList.remove('navbar-shrink')
		} else {
			navbarCollapsible.classList.add('navbar-shrink')
		}

	};

	// Shrink the navbar 
	navbarShrink();

	// Shrink the navbar when page is scrolled
	document.addEventListener('scroll', navbarShrink);

	// Activate Bootstrap scrollspy on the main nav element
	const mainNav = document.body.querySelector('#mainNav');
	if (mainNav) {
		new bootstrap.ScrollSpy(document.body, {
			target: '#mainNav',
			offset: 74,
		});
	};

	// Collapse responsive navbar when toggler is visible
	const navbarToggler = document.body.querySelector('.navbar-toggler');
	const responsiveNavItems = [].slice.call(
		document.querySelectorAll('#navbarResponsive .nav-link')
	);
	responsiveNavItems.map(function (responsiveNavItem) {
		responsiveNavItem.addEventListener('click', () => {
			if (window.getComputedStyle(navbarToggler).display !== 'none') {
				navbarToggler.click();
			}
		});
	});

});

$(document).ready(function () {
	$('#datatable').DataTable({
		order: [[0, 'asc']],
	});
});

$(document).ready(function() {
	$('#skills-datatable').DataTable( {
		order: [[0, 'asc']],
		"autoWidth": false,
		"pageLength": 100,
		columnDefs: [
		{
			target: 0,
			visible: false,
			searchable: true,
		}],
		rowGroup: {
			dataSrc: 0
		},
 
	} );
} );

$(document).ready(function () {
	$('#members-datatable').DataTable({
		order: [[1, 'asc']],
		dom: 'frtipB',
		buttons: [
			'copy', 'csv'
		],
		columnDefs: [
			{
				target: 5,
				visible: false,
				searchable: true,
			},
			{
				target: 6,
				visible: false,
				searchable: true,
			},
			{
				target: 7,
				visible: false,
				searchable: true,
			}
		],
	});
});

$(document).ready(function () {
	$('#alert-table').DataTable({
		order: [[5, 'desc']],
		dom: 'frtipB',
		buttons: [
			'copy', 'csv'
		],
		columnDefs: [{
			target: 6,
			visible: false,
			searchable: true,
		},
		{
			target: 7, 
			visible: false,
			searchable: true
		}],
		"fnRowCallback": function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
		  if (aData[6] == "True") {
			$('td', nRow).css('background-color', 'DarkSlateGray');
			$('td', nRow).css('color', 'White');
		  }
		}
	});
});

$(document).ready(function () {
	$('#datatable-extended').DataTable({
		language: { search: "Search:  " },
		"paging": false,
		"bLengthChange" : false,
		order: [[1, 'desc']],
	});
});

$(document).ready(function() {
	$('#datatable-assigned-profiles').DataTable( {
		order: [[0, 'asc']],
		lengthChange: false,
		columnDefs: [
		{
			target: 0,
			visible: false,
			searchable: true,
		}],
		rowGroup: {
			dataSrc: 0
		},
	});
});

$(document).ready(function() {
	$('#datatable-trello').DataTable( {
		"autoWidth": false,
		"bLengthChange": false,
		"searching": false,
	} );
} );

$(document).ready(function() {
	$('#datatable-assigned-badges').DataTable( {
		order: [[0, 'asc']],
		"autoWidth": false,
		columnDefs: [
		{
			target: 0,
			visible: false,
			searchable: true,
		}],
		rowGroup: {
			dataSrc: 0
		},
 
	} );
} );

$(document).ready(function() {
	$('#datatable-member-assignments').DataTable( {
		order: [[2, 'asc']],
		"bLengthChange": false,
		"searching": false,
	} );
} );

$(document).ready(function() {
	$('#datatable-active-assignments').DataTable( {
		order: [[0, 'asc']],
		"bLengthChange": false,
		"searching": false,
	} );
} );

$(document).ready(function() {
	$('#datatable-active-simscos').DataTable( {
		order: [[0, 'asc']],
		"bLengthChange": false,
		"searching": false,
		"bInfo": false,
		paging: false
	} );
} );

$(document).ready(function() {
	$('#datatable-deployed-im').DataTable( {
		order: [[0, 'asc']],
		"bLengthChange": false,
		"searching": false,
		"bInfo": false,
		paging: false
	} );
} );

$(document).ready(function() {
	$('#datatable-privacy-policy').DataTable( {
		"bLengthChange": false,
		"searching": false,
	} );
} );

$(document).ready(function() {
	$('#datatable-op-reviews').DataTable( {
		order: [[3, 'asc']],
		"bLengthChange": false,
		"searching": false,
	} );
} );

$(document).ready(function () {
	$('#datatable-full-portfolio').DataTable({
		language: { search: "Search:  " },
		"bLengthChange" : false,
	});
});

$(function(){
	$(".typed").typed({
		strings: ["infographics.", "mobile data collection.", "basemaps."],
		// Optionally use an HTML element to grab strings from (must wrap each string in a <p>)
		stringsElement: null,
		// typing speed
		typeSpeed: 30,
		// time before typing starts
		startDelay: 1200,
		// backspacing speed
		backSpeed: 20,
		// time before backspacing
		backDelay: 500,
		// loop
		loop: true,
		// false = infinite
		loopCount: 5,
		// show cursor
		showCursor: false,
		// character for cursor
		cursorChar: "|",
		// attribute to type (null == text)
		attr: null,
		// either html or text
		contentType: 'html',
		// call when done callback function
		callback: function() {},
		// starting callback function before each string
		preStringTyped: function() {},
		//callback for every typed string
		onStringTyped: function() {},
		// callback for reset
		resetCallback: function() {}
	});
});

$(document).ready(function() {
  $("h5").html(function(_, html) {
	return html.replace(/(\#\w+)/g, '<span class="tweet">$1</span>');
  });
});