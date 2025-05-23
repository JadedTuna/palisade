high secret = true;
low secretSteal = false;
try {
    if(secret) {
        throw;
    }
} catch {
    secretSteal = true;
}