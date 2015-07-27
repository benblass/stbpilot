/*================================
*GEO MESHING
*------------
*
*b.blassel@gmail.com
*
*Set of tools to mesh a given geographical zone in elements of a given size
*
*V0.1 - Elements are rectangles in a lat/long referential, of a given size.
*Rectangles of at least 3 points included in the target zone are returned.
*
*==================================*/

	/*MESHING
	/========*/

	function mesh(zone, element_size_x, element_size_y){
		var elements = [];
		
		var bounding_box = find_bounding_box(zone);

		if (element_size_x == undefined) 
			element_size_x = Math.abs((bounding_box[2][0] - bounding_box[0][0]))/10;
	
		if (element_size_y == undefined)
			element_size_y = Math.abs((bounding_box[0][1] - bounding_box[2][1]))/10; 

		var grid = grid_box(bounding_box, element_size_x, element_size_y);

		var elements = approach_by_triangle(grid, polygon);

		return elements;
	}

	/*RAYTRACING
	*===========
	/*Functions to confirm the inclusion of a point in a given polygon

		/*
		segs_interesct (seg1, seg2)

		Cehcks whether 2 segments intersect.
		returns:
		- false if they don't
		- [x,y] coordinates of inttersection if intersection is unique
		- true if they are at least partly confunded
		*/

		function segs_intersect (seg1, seg2) {
			var seg1_pt_A = seg1[0];
			var seg1_pt_B = seg1[1];

			var seg2_pt_X = seg2[0];
			var seg2_pt_Y = seg2[1];

			var a1 = (seg1_pt_A[1] - seg1_pt_B[1]) / (seg1_pt_A[0] - seg1_pt_B[0]);
			var b1 = seg1_pt_A[1]-a1*seg1_pt_A[0];

			var a2 = (seg2_pt_X[1] - seg2_pt_Y[1]) / (seg2_pt_X[0] - seg2_pt_Y[0]);
			var b2 = seg2_pt_X[1]-a2*seg2_pt_X[0];

			//Generic case for the intersection of the lines

			var x = (b2-b1)/(a1-a2);
			var y = a1*x+b1;
			
			//In case lines are parallel and distinct

			if ((a1 == a2) && (b1 != b2)) {
				return false;
			}

			//in case both segments are on the same line
			if ((a1==a2) && (b1==b2)) {

				var max1 = Math.max(seg1_pt_A[0], seg1_pt_B[0]);
				var min1 = Math.min(seg1_pt_A[0], seg1_pt_B[0]);

				var max2 = Math.max(seg2_pt_X[0], seg2_pt_Y[0]);
				var min2 = Math.min(seg2_pt_X[0], seg2_pt_Y[0]);

				if (((min1 <= max2) && (min1>=min2)) || ((min2 <= max1) && (min2>=min1)))
					return true;
				return false;
			}

			//case of verticals

			if (seg1_pt_A[0] == seg1_pt_B[0]) { //seg1 is vertical, x,y are infinity
				//intersection
				x = seg1_pt_A[0];
				y = a2*x+b2;
			}

			if (seg2_pt_X[0] == seg2_pt_Y[0]) {
				//intersection
				x = seg2_pt_X[0];
				y = a1*x+b1;
			}

			if ((seg2_pt_X[0] == seg2_pt_Y[0]) && (seg1_pt_A[0] == seg1_pt_B[0])){
				var top1 = Math.max(seg1_pt_A[1], seg1_pt_B[1]);
				var bot1 = Math.min(seg1_pt_A[1], seg1_pt_B[1]);

				var top2 = Math.max(seg2_pt_X[1], seg2_pt_Y[1]);
				var bot2 = Math.min(seg2_pt_X[1], seg2_pt_Y[1]);

				if (((bot1 <= top2) && (bot1>=bot2)) || ((bot2 <= top1) && (bot2>=bot1)))
					return true;

				return false;
			}

			if ( (x <= Math.max(seg1_pt_A[0], seg1_pt_B[0]) ) && (x >= Math.min(seg1_pt_A[0], seg1_pt_B[0]))) {
				if ((x<=Math.max(seg2_pt_X[0], seg2_pt_Y[0]))&&(x>= Math.min(seg2_pt_X[0], seg2_pt_Y[0]))) {
					return [x,y];
				}
			}
			return false;
		}

		function seg_intersect_poly(seg, poly){

			var num_intersect=0;

			for(var i=0; i<poly.length; i++){
				poly_segment = [poly[i], poly[(i+1)%poly.length]];

				if (segs_intersect(seg, poly_segment) != false){
					num_intersect++;
				}
			}

			return num_intersect;
		}

		function is_pt_inside(pt, poly) {

			var sections = seg_intersect_poly([pt, [90,0]], poly);

			if ((sections%2==0))
				return false;

			return true;
		}

	/*INITIAL MESH / BASIC MATH UTILS
	*=================================
	*Generates a mesh on a bounding area, from which a finer meshing will be selected
	*/

		function find_bounding_box(polyarray) {

			var max_lng = 0;
			var max_lat = 0;

			var min_lng = 400;
			var min_lat = 400;

			for(var i=0;i<polyarray.length; i++) {
				pt = polyarray[i];
				if (pt[0] > max_lng) { max_lng = pt[0]; }
				if (pt[1] > max_lat) { max_lat = pt[1]; }
				if (pt[0] < min_lng) { min_lng = pt[0]; }
				if (pt[1] < min_lat) { min_lat = pt[1]; }
			}

			return [[min_lng,max_lat],[max_lng,max_lat],[max_lng, min_lat],[min_lng, min_lat]];
		}


		function range(a,b,step) {

			if(step == undefined)  {
				return [Math.min(a,b), Math.max(a,b)];
			}

			if(step > Math.abs(b-a))  {
				return [Math.min(a,b), Math.max(a,b)];
			}

			var range_ = [];

			for (i=0; (a + i*step < b ); i++) {
				range_.push(a+i*step);
			}

			range_.push(b);

			return range_;

		}

		function grid_box(box,stepx, stepy) {
			//Returns a list of squares mapping

			var top_left_X = box[0][0];
			var top_left_Y = box[0][1];

			var top_right_X = box[0][0];
			var top_right_Y =box[0][1];

			var bot_left_X = box[0][0];
			var bot_left_Y = box[0][1];


			if (stepx == undefined)
				stepx = (top_right_X - top_left_X) / 10;

			if (stepy == undefined)
				stepy = (top_left_Y - bot_left_Y) / 10;

			for(i=0; i<box.length; i++){
				//test top left: min X, max Y

				if(box[i][0]<= top_left_X && box[i][1] >= top_left_Y) {
					top_left_X = box[i][0];
					top_left_Y = box[i][1];
				}

				//test top right: max x, max Y

				if(box[i][0]>= top_right_X && box[i][1] >= top_right_Y) {
					top_right_X = box[i][0];
					top_right_Y = box[i][1];
				}

				//test bot_left, minx, min y

				if(box[i][0]<= bot_left_X && box[i][1] <= bot_left_Y) {
					bot_left_X = box[i][0];
					bot_left_Y = box[i][1];
				}
			}

			var grid_box = [];

			var rangex = range(top_left_X, top_right_X, stepx);
			var rangey = range(bot_left_Y, top_left_Y, stepy);

			//this can probably be optimised in terms of number of operations
			for (yindex=0; yindex < rangey.length-1; yindex++ ){
				for(xindex =0; xindex < rangex.length-1; xindex++) {
					grid_box.push([[rangex[xindex], rangey[yindex]], [rangex[xindex+1], rangey[yindex]], [rangex[xindex+1], rangey[yindex+1]], [rangex[xindex], rangey[yindex+1]]]);
				}
			}

			return grid_box;

		}

	/*FINE RECTANGLE MESHING
	*====================
	*From a rough rectangle meshing, selects the appropriate elements and returns center
	*/

		function is_poly_contained(poly, container) {

			var is_poly_contained = true;	
			var not_included = 0;

			for(i=0; i< poly.length; i++) {
				if (!is_pt_inside(poly[i], container)){
					is_poly_contained = false;
					not_included++;
				}
			}

			return [is_poly_contained, not_included]
		}

		function approach_by_triangle(polyarray, container){

			var intersect = [];

			for(var i=0; i<polyarray.length; i++) {

				var result = is_poly_contained(polyarray[i], container);

				if (result[0] || (!result[0] && result[1] == 1)) {
					var center_pt =  [(polyarray[i][0][0] + polyarray[i][2][0])/2 , (polyarray[i][0][1] + polyarray[i][2][1])/2];
					intersect.push([polyarray[i], center_pt]);
				}
			}
			return intersect;

		}