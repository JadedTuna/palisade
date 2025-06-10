in {
	high x: int;
	high b: bool;
}
out {
	low y: bool;
}

fn proc(x: int, y: bool) bool {
	if (y) {
		return true;
	} else {
		return false;
	}
}

y = proc(x, b);
