
var inSearchMode = false;

function zone_selected(e) {
	index = e.target.feature.properties.index;

	$('#search_button').text('Initiate search on flight zone: ' + flight_zones.features[index].properties.flname);
	$('#search_button').addClass("activated");

	$('#search_button').on('click', function () { 
		map_searchconfig(e);
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
	inSearchMode = true;

	return;
}
