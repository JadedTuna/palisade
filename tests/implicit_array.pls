in {
	high secret: bool;
}
out {
	low arr[3]: bool;
}

x := 10;
y := false;
if (secret) {
	y = true;
}

arr[x] = y;
