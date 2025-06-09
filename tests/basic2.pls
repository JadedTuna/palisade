in {}
out {
    low err: bool;
}

num := -3;
total := 34;
err = false;
try {
    if (num < 0) {
        throw;
    }
    total = total + num;
} catch {
    err = true;
}
