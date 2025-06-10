in {
    high arg: bool;
}
out {
    low arr[3]: bool;
}

x[3] := [false, true, arg];
// error, must specify size for z
z := x;
