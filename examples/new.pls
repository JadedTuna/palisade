in {
    low x: int;
    high y: int;
}
out {
    low z: int;
    high p: bool;
}

if (y) {
    if (x) {
        z = 9;
    } else {
        z = y;
    }
} else {
    z = x;
}

// z should be HIGH
