in {
    high secret: bool;
}
out {
    low exfil: bool;
}

fn foo() int {
    throw;
    return 42;
}

exfil = false;
try {
    if (secret) {
        z := foo();
    }
} catch {
    exfil = true;
}
