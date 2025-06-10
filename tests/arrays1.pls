in {
    high arg: bool;
}
out {
    low arr[3]: bool;
}

// array assignments are done by-value (copy)
x[3] := [false, true, arg];
y[3] := arr;
arr = x;
arr = y;
