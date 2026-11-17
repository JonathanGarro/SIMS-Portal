// DataTables 2 defaults that match production's DataTables 1 tables: "Previous / Next"
// pagination and the "Show _ entries" length label (#158 follow-up)
if (window.DataTable) {
	$.extend(true, DataTable.defaults, {
		pagingType: 'simple_numbers',
		language: {
			lengthMenu: 'Show _MENU_ entries',
			paginate: {previous: 'Previous', next: 'Next'},
		},
	});
}

// fade flash alerts after 5 seconds
window.setTimeout(function() {
	$("#alert").fadeTo(500, 0) 
}, 6000);

// Bootstrap 5 tooltips are opt-in: initialise every element that asks for one
document.addEventListener('DOMContentLoaded', function () {
	document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
		new bootstrap.Tooltip(el);
	});
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
$(document).ready(function () {
	$('#emergencyDatatable').DataTable({
		order: [[5, 'desc']],
		columnDefs: [
			{ targets: [5], visible: false }
		]
	});
});

$(document).ready(function () {
	$('#logs-datatable').DataTable({
		order: [[0, 'desc']],
		lengthChange: true,
		searching: true,
		pageLength: 100,
		// DataTables 2 equivalent of the legacy dom: 'frtipB' (search, table, info,
		// paging, then the export buttons below; no page-length menu)
		layout: { topStart: null, topEnd: 'search', bottomStart: 'info', bottomEnd: 'paging', bottom2Start: 'buttons' },
		buttons: [
			'copy', 'csv'
		],
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
		// DataTables 2 equivalent of the legacy dom: 'frtipB' (search, table, info,
		// paging, then the export buttons below; no page-length menu)
		layout: { topStart: null, topEnd: 'search', bottomStart: 'info', bottomEnd: 'paging', bottom2Start: 'buttons' },
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
		// DataTables 2 equivalent of the legacy dom: 'frtipB' (search, table, info,
		// paging, then the export buttons below; no page-length menu)
		layout: { topStart: null, topEnd: 'search', bottomStart: 'info', bottomEnd: 'paging', bottom2Start: 'buttons' },
		buttons: [
			'copy', 'csv'
		],
		
		
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
	$('#datatable-admins').DataTable( {
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
		order: [[2, 'desc']],
		"bLengthChange": false,
		"searching": false,
	} );
} );

$(document).ready(function() {
	var table = $('#datatable-documentation').DataTable({
		order: [[0, 'asc']],
		"bLengthChange": false
	});

	// dropdown filter for the "Category" column in the table header
	table.columns(1).every(function() {
		var column = this;
		var select = $('<select><option value="">Category</option></select>') // Add the default option
			.appendTo($(column.header()).empty())
			.on('change', function() {
				var val = DataTable.util.escapeRegex(
					$(this).val()
				);

				column
					.search(val ? '^' + val + '$' : '', true, false)
					.draw();
			});

		// add distinct values from the "Category" column to the dropdown
		column
			.data()
			.unique()
			.sort()
			.each(function(d, j) {
				select.append('<option value="' + d + '">' + d + '</option>');
			});
	});
});

$(document).ready(function() {
	$('#datatable-active-emergencies').DataTable( {
		order: [[0, 'asc']],
		"bLengthChange": false,
		"searching": false,
		"paging": false,
		"info": false,
	} );
} );

$(document).ready(function() {
	$('#datatable-active-assignments').DataTable( {
		order: [[0, 'asc']],
		"bLengthChange": false,
		"searching": false,
		"paging": false,
		"info": false,
	} );
} );

$(document).ready(function() {
	$('#datatable-active-simscos').DataTable( {
		order: [[2, 'asc']],
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

$(document).ready(function() {
  $("h5").html(function(_, html) {
	return html.replace(/(\#\w+)/g, '<span class="tweet">$1</span>');
  });
});