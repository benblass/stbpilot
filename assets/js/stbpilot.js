
function zone_selected(index) {
	$('#search_button').text('Initiate search on flight zone: ' + flight_zones.features[index].properties.flname);
	$('#search_button').addClass("activated");
	$('#search_button').on('click', function () { 
		initiate_search(index);
		}
	);
	return;
}

function zone_unselected() {
	$('#search_button').text("Search");
	$('#search_button').removeClass("activated");
	$('#search_button').off();
	return;
}

function initiate_search(index) {
	$('#search_button').addClass('clicked');
	$('#search_button').removeClass('activated');
	$('#search_button').off();

	$.post('/initial_search', {flindex: index});

	$("#result").text("Initiating search on Flight Zone " + flight_zones.features[index].properties.flname);
	return;
}
