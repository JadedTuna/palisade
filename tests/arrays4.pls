in {
	high secret: bool;
}
out {
	low arr[3]: bool;
}

x := 2;
y := false;
if (secret) {
	y = true;
}

arr[x] = y;
