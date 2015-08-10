function hsl2rgb(h, s, l) {
	var m1, m2, hue;
	var r, g, b
	s /=100;
	l /= 100;
	if (s == 0)
		r = g = b = (l * 255);
	else {
		if (l <= 0.5)
    		m2 = l * (s + 1);
		else
    		m2 = l + s - l * s;

		m1 = l * 2 - m2;
		hue = h / 360;
		r = Math.round(HueToRgb(m1, m2, hue + 1/3));
		g = Math.round(HueToRgb(m1, m2, hue));
		b = Math.round(HueToRgb(m1, m2, hue - 1/3));
	}
return [r,g,b];
}

function HueToRgb(m1, m2, hue) {
	var v;
	if (hue < 0)
		hue += 1;
	else if (hue > 1)
		hue -= 1;

	if (6 * hue < 1)
		v = m1 + (m2 - m1) * hue * 6;
	else if (2 * hue < 1)
		v = m2;
	else if (3 * hue < 2)
		v = m1 + (m2 - m1) * (2/3 - hue) * 6;
	else
		v = m1;

	return 255 * v;
}

var hexChar = ["0", "1", "2", "3", "4", "5", "6", "7","8", "9", "A", "B", "C", "D", "E", "F"];

	function byteToHex(b) {
		return hexChar[(b >> 4) & 0x0f] + hexChar[b & 0x0f];
}

function gradient(value, max, min) {
	/* value: measured value, s: saturation, l: light, max/min: magnitude range; start/end: hsl range */
		
		var s = 100;
		var l = 50;

		var start = 180;
		var end = 0;

		value = ((value - min) * (start - end) / (max-min)) + end;

		color = hsl2rgb(value, s, l);

		return '#'+ byteToHex(color[0])+ byteToHex(color[1]) + byteToHex(color[2]);
	}