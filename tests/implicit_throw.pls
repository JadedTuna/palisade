in {
    high secret: bool;
}
out {
    low secretSteal: bool;
}

secretSteal = false;
try {
    if (secret) {
        throw;
    }
} catch {
    secretSteal = true;
}
