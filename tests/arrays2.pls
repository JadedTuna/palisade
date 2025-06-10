in {
    high arg: bool;
}
out {
    low arr[3]: bool;
}

x[3] := [false, true, arg];
// error: size mismatch
y[4] := arr;
